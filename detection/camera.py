import cv2
import numpy as np
import threading
import time
import base64
import re
import os
import io
from PIL import Image
from django.utils import timezone
from django.conf import settings
from access.logic import process_detection, clean_plate
from access.models import AccessLog, ParkingConfig


class LicensePlateDetector:
    def __init__(self):
        # Initialize Gemini API with google.generativeai library
        self.model = None
        api_key = os.environ.get('GEMINI_API_KEY')
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-flash-lite-latest')
            except ImportError:
                print("Warning: google.generativeai not installed. Install with: pip install google-generativeai")
            except Exception as e:
                print(f"Warning: Gemini initialization failed: {e}")
        else:
            print("Warning: GEMINI_API_KEY not set. License plate detection will not work.")
        
        self.cap = None
        self.running = False
        self.last_frame = None
        self.last_result = {}
        self.thread = None
        self.fallback_frames = []
        self.fallback_index = 0
        self.current_gate = 'MAIN'
        self._load_fallback_frames()
    
    def _load_fallback_frames(self):
        """Load test images for fallback mode."""
        test_frames_dir = settings.MEDIA_ROOT / 'test_frames'
        if test_frames_dir.exists():
            self.fallback_frames = sorted([
                str(f) for f in test_frames_dir.glob('*.jpg')
            ])
            print(f"Loaded {len(self.fallback_frames)} fallback frames from {test_frames_dir}")
        else:
            print(f"Test frames directory not found: {test_frames_dir}")



    
    def preprocess_frame(self, frame):
        """Preprocess frame for better license plate visibility."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        return gray, enhanced, frame
    
    def read_plate_with_gemini(self, frame):
        """Use Gemini Flash Lite to extract license plate number from frame."""
        if not self.model:
            print("Gemini model not initialized!")
            return '', 0.0
        
        try:
            # Convert OpenCV frame (BGR) to PIL Image (RGB)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Build the prompt for license plate extraction
            prompt = """Analyze this image and extract the vehicle registration/license plate number, or any prominent text/numbers written on paper (for testing).

Instructions:
1. Look carefully for any license plate, registration number, or handwritten numbers/text clearly visible in the image.
2. Extract ONLY the alphanumeric characters of the plate/registration number or the written text on the paper.
3. Return ONLY the extracted text/numbers, nothing else.
4. If you find a plate or paper with writing, respond with just the text (e.g., "16TAC123").
5. If no plate or prominent text is found, respond with "NO_PLATE_FOUND".
6. Ignore any other background text in the image - focus only on the main focal point (plate or handheld paper).

Examples:
- If you see "16TAC123" → respond: 16TAC123
- If you see handwritten "ABC1234" on paper → respond: ABC1234
- If you see nothing recognizable → respond: NO_PLATE_FOUND"""
            
            print("Sending request to Gemini...")
            # Generate content - pass prompt and image directly
            response = self.model.generate_content([prompt, pil_image])
            
            try:
                result_text = response.text.strip()
                print(f"Gemini raw response: '{result_text}'")
            except Exception as e:
                print(f"Could not read response.text (might be blocked by safety filters). Feedback: {response.prompt_feedback}")
                return '', 0.0
            
            if result_text == "NO_PLATE_FOUND" or not result_text:
                return 'NO_PLATE_FOUND', 0.0  # Return 'NO_PLATE_FOUND' clearly instead of empty string
            
            # Clean the result - remove spaces and special characters, keep only alphanumeric
            plate_text = re.sub(r'[^A-Z0-9]', '', result_text.upper())
            print(f"Cleaned plate text: '{plate_text}'")
            
            if plate_text:
                # Confidence: if Gemini returned a result, assume high confidence
                confidence = 0.85
                print(f"✓ Gemini extracted plate: {plate_text}")
                return plate_text, confidence
            
            return '', 0.0
            
        except Exception as e:
            print(f"Gemini API Error: {e}")
            import traceback
            traceback.print_exc()
            return '', 0.0
    
    def annotate_frame(self, frame, detection_result):
        """Annotate frame with detection results."""
        annotated = frame.copy()
        
        plate_text = detection_result.get('plate', '')
        confidence = detection_result.get('confidence', 0.0)
        decision = detection_result.get('decision', '')
        
        # Get parking config
        config, _ = ParkingConfig.objects.get_or_create(defaults={'max_capacity': 50})
        status = "OPEN" if not config.is_manual_closed and config.is_within_hours() else "CLOSED"
        if config.is_full():
            status = "FULL"
        
        # Draw HUD with detection info
        if plate_text:
            hud_text = f"Plate: {plate_text} | Conf: {confidence:.2f} | Decision: {decision} | Status: {status}"
            color = (0, 255, 0) if decision == "GRANTED" else (0, 0, 255)
        else:
            hud_text = f"No plate detected | Status: {status}"
            color = (255, 255, 0)
        
        cv2.putText(annotated, hud_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return annotated
    
    def process_frame(self, frame, use_ai=False):
        """Process single frame. Uses AI only when use_ai is True to avoid rate limits."""
        result = {
            'frame': frame,
            'plate': '',
            'confidence': 0.0,
            'decision': 'UNKNOWN',
            'reason': '',
            'vehicle_name': '',
        }
        
        if use_ai:
            # Use Gemini to detect and read license plate
            plate_text, confidence = self.read_plate_with_gemini(frame)
            
            result['plate'] = plate_text
            result['confidence'] = confidence
            
            print(f"Gemini Detection: plate={plate_text}, confidence={confidence:.2f}")
            
            # Only process if plate was detected and it's not NO_PLATE_FOUND
            if plate_text and plate_text != 'NO_PLATE_FOUND':
                detection_result = process_detection(plate_text, confidence, numpy_frame=frame, gate_name=self.current_gate)
                result['decision'] = detection_result['decision']
                result['reason'] = detection_result['reason']
                if detection_result['vehicle']:
                    result['vehicle_name'] = detection_result['vehicle'].owner_name
                
                print(f"Access Decision: {result['decision']} - {result['reason']}")
            elif plate_text == 'NO_PLATE_FOUND':
                result['decision'] = 'NOT FOUND'
                result['reason'] = 'AI could not find a plate in the image'
                result['plate'] = 'None'
                result['vehicle_name'] = '-'
            
            self.last_result = result.copy()
        else:
            # Keep previous results for displaying on the HUD if we don't query AI
            if self.last_result:
                result['plate'] = self.last_result.get('plate', '')
                result['confidence'] = self.last_result.get('confidence', 0.0)
                result['decision'] = self.last_result.get('decision', 'UNKNOWN')
                result['reason'] = self.last_result.get('reason', '')
                result['vehicle_name'] = self.last_result.get('vehicle_name', '')
        
        # Annotate frame
        annotated = self.annotate_frame(frame, result)
        self.last_frame = annotated
        
        return result
    
    def capture_loop(self):
        """Main capture loop running in background thread."""
        while self.running:
            try:
                frame = None
                
                if self.fallback_frames and (settings.FALLBACK_MODE or self.cap is None):
                    frame_path = self.fallback_frames[self.fallback_index]
                    frame = cv2.imread(frame_path)
                    if frame is None:
                        print(f"Failed to load frame: {frame_path}")
                        self.fallback_index = (self.fallback_index + 1) % len(self.fallback_frames)
                        time.sleep(0.1)
                        continue
                    self.fallback_index = (self.fallback_index + 1) % len(self.fallback_frames)
                    time.sleep(0.5)
                else:
                    ret, frame = self.cap.read()
                    if not ret or frame is None:
                        print("Failed to read frame from camera")
                        break
                
                # Do NOT use AI automatically on every frame
                self.process_frame(frame, use_ai=False)
                time.sleep(0.1)
            except Exception as e:
                print(f"Capture loop error: {e}")
                break
    
    def start_stream(self):
        """Start the video stream."""
        if self.running:
            return
        
        self.cap = None
        
        if not settings.FALLBACK_MODE:
            from access.models import Gate
            gate_qs = Gate.objects.filter(is_active=True)
            if self.current_gate != 'MAIN':
                gate_qs = gate_qs.filter(name__iexact=self.current_gate)
            gate = gate_qs.first()
            
            if gate and gate.camera_ip:
                rtsp = gate.rtsp_url()
                print(f"Connecting to RTSP: {rtsp}")
                self.cap = cv2.VideoCapture(rtsp)
            else:
                print(f"Gate '{self.current_gate}' has no camera IP, falling back to webcam")
                self.cap = cv2.VideoCapture(0)
            
            if self.cap is None or not self.cap.isOpened():
                print("Warning: Camera not available")
                self.cap = None
        
        if self.cap is None and self.fallback_frames:
            print("Using fallback test frames")
        elif self.cap is None:
            print("Error: No camera and no fallback frames available")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.thread.start()
    
    def stop_stream(self):
        """Stop the video stream."""
        self.running = False
        if self.cap:
            self.cap.release()
    
    def encode_frame(self, frame):
        """Encode frame to base64 JPEG string."""
        if frame is None:
            return ''
        
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            return frame_b64
        return ''


_detector_instance = None


def get_detector():
    """Get global detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = LicensePlateDetector()
    return _detector_instance
