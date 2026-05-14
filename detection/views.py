from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import base64


@login_required
def live_view(request):
    context = {
        'ws_url': 'ws://localhost:8000/ws/detection/',
    }
    return render(request, 'detection/live.html', context)


@login_required
@require_http_methods(['POST'])
def manual_trigger(request):
    """Process manual frame upload/trigger."""
    import cv2
    import numpy as np
    from detection.camera import get_detector
    from access.logic import process_detection
    
    detector = get_detector()
    
    try:
        if 'image' in request.FILES:
            image_file = request.FILES['image']
            file_bytes = np.frombuffer(image_file.read(), np.uint8)
            frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        elif request.POST.get('frame'):
            frame_b64 = request.POST.get('frame')
            frame_data = base64.b64decode(frame_b64)
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            return JsonResponse({'error': 'No frame provided'}, status=400)
        
        if frame is None:
            return JsonResponse({'error': 'Invalid image'}, status=400)
        
        result = detector.process_frame(frame)
        
        return JsonResponse({
            'plate': result['plate'],
            'decision': result['decision'],
            'reason': result['reason'],
            'confidence': round(result['confidence'], 2),
            'vehicle_name': result['vehicle_name'],
            'success': True,
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
