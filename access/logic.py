import re
from datetime import datetime
from django.db import models
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


def process_detection(plate_string, confidence, snapshot_path=None, numpy_frame=None, gate_name='MAIN'):
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
    
    from .models import Gate, Zone
    
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
            gate=gate_name,
        )
        result['log'] = log
        return result
    
    clean_plate_str = clean_plate(plate_string)
    result['plate'] = clean_plate_str
    
    # Resolve gate and its zone
    try:
        gate = Gate.objects.select_related('zone').get(
            name__iexact=gate_name, is_active=True
        )
        use_gate = True
    except Gate.DoesNotExist:
        gate = None
        use_gate = False
    
    global_config, _ = ParkingConfig.objects.get_or_create(
        defaults={
            'open_time': '07:00',
            'close_time': '22:00',
            'max_capacity': 50,
        }
    )
    
    if global_config.is_manual_closed:
        result['reason'] = 'MANUAL_CLOSED'
        log = AccessLog.objects.create(
            plate_detected=clean_plate_str,
            event_type='DENIED',
            denial_reason='MANUAL_CLOSED',
            confidence_score=confidence,
            processed_by='AUTO',
            gate=gate_name,
        )
        result['log'] = log
        return result
    
    # Check gate operating hours
    if use_gate and not global_config.is_manual_open and not gate.is_within_hours():
        result['reason'] = 'OUTSIDE_HOURS'
        log = AccessLog.objects.create(
            plate_detected=clean_plate_str,
            event_type='DENIED',
            denial_reason='OUTSIDE_HOURS',
            confidence_score=confidence,
            processed_by='AUTO',
            gate=gate_name,
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
    
    if not vehicle.is_subscription_active():
        result['reason'] = 'SUBSCRIPTION_EXPIRED'
        log = AccessLog.objects.create(
            vehicle=vehicle,
            plate_detected=clean_plate_str,
            event_type='DENIED',
            denial_reason='SUBSCRIPTION_EXPIRED',
            confidence_score=confidence,
            processed_by='AUTO',
        )
        result['log'] = log
        return result
    
    if not vehicle.can_enter_today():
        result['reason'] = 'DAILY_LIMIT_REACHED'
        log = AccessLog.objects.create(
            vehicle=vehicle,
            plate_detected=clean_plate_str,
            event_type='DENIED',
            denial_reason='DAILY_LIMIT_REACHED',
            confidence_score=confidence,
            processed_by='AUTO',
            gate=gate_name,
        )
        result['log'] = log
        return result
    
    # Zone capacity check
    if use_gate and gate.zone:
        capacity_check = gate.zone
    else:
        capacity_check = global_config
    
    if capacity_check.is_full():
        result['reason'] = 'PARKING_FULL'
        log = AccessLog.objects.create(
            vehicle=vehicle,
            plate_detected=clean_plate_str,
            event_type='DENIED',
            denial_reason='PARKING_FULL',
            confidence_score=confidence,
            processed_by='AUTO',
            gate=gate_name,
        )
        result['log'] = log
        return result
    
    # Check vehicle type against gate restrictions
    if use_gate and not gate.allows_vehicle_type(vehicle.vehicle_type):
        result['reason'] = 'VEHICLE_TYPE_NOT_ALLOWED'
        log = AccessLog.objects.create(
            vehicle=vehicle,
            plate_detected=clean_plate_str,
            event_type='DENIED',
            denial_reason='VEHICLE_TYPE_NOT_ALLOWED',
            confidence_score=confidence,
            processed_by='AUTO',
            gate=gate_name,
        )
        result['log'] = log
        return result
    
    result['decision'] = 'GRANTED'
    result['event_type'] = 'ENTRY'
    result['reason'] = 'Entry granted'
    result['vehicle'] = vehicle
    
    capacity_check.current_count = models.F('current_count') + 1
    capacity_check.save()
    
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
        gate=gate_name,
        zone=gate.zone if use_gate and gate.zone else None,
    )
    result['log'] = log
    
    return result


def process_exit(plate_string, gate_name='MAIN'):
    """
    Process vehicle exit.
    Finds most recent ENTRY for this plate with no matching EXIT.
    """
    from .models import Gate, Zone
    
    clean_plate_str = clean_plate(plate_string)
    
    try:
        gate = Gate.objects.select_related('zone').get(
            name__iexact=gate_name, is_active=True
        )
        use_gate = True
    except Gate.DoesNotExist:
        gate = None
        use_gate = False
    
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
                gate=gate_name,
                zone=gate.zone if use_gate and gate.zone else None,
            )
            
            config.current_count = models.F('current_count') - 1
            config.save()
            
            if use_gate and gate.zone:
                Zone.objects.filter(pk=gate.zone.pk).update(
                    current_count=models.F('current_count') - 1
                )
            
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
