from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from access.models import ParkingConfig


@require_http_methods(['GET'])
def api_parking_status(request):
    """API endpoint to get current parking status."""
    config, _ = ParkingConfig.objects.get_or_create(
        defaults={
            'open_time': '07:00',
            'close_time': '22:00',
            'max_capacity': 50,
        }
    )
    
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
    
    return JsonResponse({
        'status': status,
        'count': config.current_count,
        'capacity': config.max_capacity,
        'occupancy': config.occupancy_pct(),
        'is_full': config.is_full(),
        'is_within_hours': config.is_within_hours(),
    })
