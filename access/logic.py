import re
from datetime import datetime
from .models import AccessLog, ParkingConfig
from vehicles.models import Vehicle
from django.core.files.base import ContentFile
import io
from PIL import Image


def clean_plate(plate_string):
    """Clean and standardize plate string."""
    if not plate_string:
        return ''
    plate = plate_string.upper()
    plate = re.sub(r'[^A-Z0-9]', '', plate)
    return plate.strip()


def save_snapshot(numpy_frame, filename):
    """Convert numpy array to PIL Image and save."""
    if numpy_frame is None:
        return None
    
    try:
        img = Image.fromarray(numpy_frame)
        image_io = io.BytesIO()
        img.save(image_io, format='JPEG')
        image_io.seek(0)
        return ContentFile(image_io.read(), name=filename)
    except Exception as e:
        print(f"Error saving snapshot: {e}")
        return None


def process_detection(plate_string, confidence, snapshot_path=None, numpy_frame=None):
    """
    Main access decision engine.
    
    Returns dict:
    {
        'plate': str,
        'decision': 'GRANTED' | 'DENIED',
        'event_type': 'ENTRY' | 'DENIED',
        'reason': str,
        'vehicle': Vehicle instance or None,
        'log': AccessLog instance
    }
    """
    
    result = {
        'plate': plate_string,
        'decision': 'DENIED',
        'event_type': 'DENIED',
        'reason': '',
        'vehicle': None,
        'log': None,
    }
    
    if confidence < 0.70:
        result['reason'] = 'LOW_CONFIDENCE'
        log = AccessLog.objects.create(
            plate_detected=clean_plate(plate_string),
            event_type='DENIED',
            denial_reason='LOW_CONFIDENCE',
            confidence_score=confidence,
            processed_by='AUTO',
        )
        result['log'] = log
        return result
    
    clean_plate_str = clean_plate(plate_string)
    result['plate'] = clean_plate_str
    
    config, _ = ParkingConfig.objects.get_or_create(
        defaults={
            'open_time': '07:00',
            'close_time': '22:00',
            'max_capacity': 50,
        }
    )
    
    if config.is_manual_closed:
        result['reason'] = 'MANUAL_CLOSED'
        log = AccessLog.objects.create(
            plate_detected=clean_plate_str,
            event_type='DENIED',
            denial_reason='MANUAL_CLOSED',
            confidence_score=confidence,
            processed_by='AUTO',
        )
        result['log'] = log
        return result
    
    if not config.is_manual_open and not config.is_within_hours():
        result['reason'] = 'OUTSIDE_HOURS'
        log = AccessLog.objects.create(
            plate_detected=clean_plate_str,
            event_type='DENIED',
            denial_reason='OUTSIDE_HOURS',
            confidence_score=confidence,
            processed_by='AUTO',
        )
        result['log'] = log
        return result
    
    try:
        vehicle = Vehicle.objects.get(plate_number__iexact=clean_plate_str)
    except Vehicle.DoesNotExist:
        result['reason'] = 'NOT_REGISTERED'
        log = AccessLog.objects.create(
            plate_detected=clean_plate_str,
            event_type='DENIED',
            denial_reason='NOT_REGISTERED',
            confidence_score=confidence,
            processed_by='AUTO',
        )
        result['log'] = log
        return result
    
    if vehicle.is_banned:
        result['reason'] = 'BANNED'
        log = AccessLog.objects.create(
            vehicle=vehicle,
            plate_detected=clean_plate_str,
            event_type='DENIED',
            denial_reason='BANNED',
            confidence_score=confidence,
            processed_by='AUTO',
        )
        result['log'] = log
        return result
    
    if not vehicle.is_registered:
        result['reason'] = 'NOT_REGISTERED'
        log = AccessLog.objects.create(
            vehicle=vehicle,
            plate_detected=clean_plate_str,
            event_type='DENIED',
            denial_reason='NOT_REGISTERED',
            confidence_score=confidence,
            processed_by='AUTO',
        )
        result['log'] = log
        return result
    
    if config.is_full():
        result['reason'] = 'PARKING_FULL'
        log = AccessLog.objects.create(
            vehicle=vehicle,
            plate_detected=clean_plate_str,
            event_type='DENIED',
            denial_reason='PARKING_FULL',
            confidence_score=confidence,
            processed_by='AUTO',
        )
        result['log'] = log
        return result
    
    result['decision'] = 'GRANTED'
    result['event_type'] = 'ENTRY'
    result['reason'] = 'Entry granted'
    result['vehicle'] = vehicle
    
    config.current_count += 1
    config.save()
    
    snapshot_file = None
    if numpy_frame is not None:
        snapshot_file = save_snapshot(
            numpy_frame,
            f'snapshot_{clean_plate_str}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
        )
    
    log = AccessLog.objects.create(
        vehicle=vehicle,
        plate_detected=clean_plate_str,
        event_type='ENTRY',
        confidence_score=confidence,
        snapshot=snapshot_file,
        processed_by='AUTO',
    )
    result['log'] = log
    
    return result


def process_exit(plate_string):
    """
    Process vehicle exit.
    Finds most recent ENTRY for this plate with no matching EXIT.
    """
    clean_plate_str = clean_plate(plate_string)
    
    config, _ = ParkingConfig.objects.get_or_create(
        defaults={
            'open_time': '07:00',
            'close_time': '22:00',
            'max_capacity': 50,
        }
    )
    
    try:
        vehicle = Vehicle.objects.get(plate_number__iexact=clean_plate_str)
    except Vehicle.DoesNotExist:
        vehicle = None
    
    try:
        entry_log = AccessLog.objects.filter(
            plate_detected=clean_plate_str,
            event_type='ENTRY',
        ).latest('timestamp')
        
        exit_exists = AccessLog.objects.filter(
            plate_detected=clean_plate_str,
            event_type='EXIT',
            timestamp__gt=entry_log.timestamp
        ).exists()
        
        if not exit_exists:
            exit_log = AccessLog.objects.create(
                vehicle=vehicle,
                plate_detected=clean_plate_str,
                event_type='EXIT',
                confidence_score=0.95,
                processed_by='AUTO',
            )
            
            config.current_count = max(0, config.current_count - 1)
            config.save()
            
            return {
                'plate': clean_plate_str,
                'decision': 'EXIT_GRANTED',
                'event_type': 'EXIT',
                'reason': 'Exit processed',
                'vehicle': vehicle,
                'log': exit_log,
            }
    except AccessLog.DoesNotExist:
        pass
    
    return {
        'plate': clean_plate_str,
        'decision': 'NO_ENTRY_FOUND',
        'event_type': 'DENIED',
        'reason': 'No matching entry found',
        'vehicle': vehicle,
        'log': None,
    }
