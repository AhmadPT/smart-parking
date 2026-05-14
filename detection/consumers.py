import asyncio
import json
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone


class ParkingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add('parking_feed', self.channel_name)
        self.frame_task = asyncio.create_task(self.send_frames_periodically())
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('parking_feed', self.channel_name)
        if hasattr(self, 'frame_task'):
            self.frame_task.cancel()
    
    async def receive(self, text_data):
        from detection.camera import get_detector
        import cv2
        import numpy as np
        
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'start':
                detector = get_detector()
                await sync_to_async(detector.start_stream)()
            
            elif action == 'stop':
                detector = get_detector()
                await sync_to_async(detector.stop_stream)()
            
            elif action == 'manual_trigger':
                frame_b64 = data.get('frame')
                if frame_b64:
                    frame_data = base64.b64decode(frame_b64)
                    nparr = np.frombuffer(frame_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        detector = get_detector()
                        # Use AI explicitly on manual trigger
                        result = await sync_to_async(detector.process_frame)(frame, use_ai=True)
                        
                        await self.send(text_data=json.dumps({
                            'type': 'manual_result',
                            'plate': result['plate'],
                            'decision': result['decision'],
                            'reason': result['reason'],
                            'confidence': result['confidence'],
                            'vehicle_name': result['vehicle_name'],
                        }))
        
        except Exception as e:
            print(f"WebSocket receive error: {e}")
    
    async def frame_update(self, event):
        """Receive frame updates from channel layer."""
        await self.send(text_data=json.dumps(event))
    
    async def send_frames_periodically(self):
        """Send frames to client periodically."""
        from detection.camera import get_detector
        
        detector = get_detector()
        frame_count = 0
        while True:
            try:
                await asyncio.sleep(0.1)
                
                # Only send if we have a frame and the detector is running
                if detector.last_frame is not None and detector.running:
                    frame_count += 1
                    
                    try:
                        frame_b64 = await sync_to_async(detector.encode_frame)(detector.last_frame)
                        
                        if not frame_b64:  # Skip if encoding failed
                            if frame_count % 50 == 0:
                                print(f"[ERROR] Frame encoding failed for frame #{frame_count}")
                            continue
                        
                        if frame_count % 10 == 0:
                            print(f"[DEBUG] Frame #{frame_count}: encoded {len(frame_b64)} bytes")
                        
                        result = detector.last_result
                        config = await sync_to_async(self._get_config)()
                        
                        msg = {
                            'type': 'frame_stream',
                            'frame': frame_b64,
                            'plate': result.get('plate', ''),
                            'decision': result.get('decision', ''),
                            'reason': result.get('reason', ''),
                            'confidence': result.get('confidence', 0),
                            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'count': config['count'],
                            'capacity': config['capacity'],
                            'status': config['status'],
                        }
                        
                        json_str = json.dumps(msg)
                        if frame_count % 10 == 0:
                            print(f"[DEBUG] JSON message size: {len(json_str)} bytes")
                        
                        await self.send(text_data=json_str)
                        
                    except Exception as inner_e:
                        print(f"[ERROR] Frame #{frame_count} - {inner_e}")
                        import traceback
                        traceback.print_exc()
                        continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[ERROR] Send frames loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(1)  # Wait before retrying
    
    def _get_config(self):
        """Get parking config (sync function wrapped for async)."""
        from access.models import ParkingConfig
        config, _ = ParkingConfig.objects.get_or_create(defaults={'max_capacity': 50})
        
        if config.is_manual_closed:
            status = "CLOSED"
        elif config.is_manual_open:
            status = "OPEN"
        elif config.is_within_hours():
            status = "OPEN"
        else:
            status = "CLOSED"
        
        if config.is_full():
            status = "FULL"
        
        return {
            'count': config.current_count,
            'capacity': config.max_capacity,
            'status': status,
        }
