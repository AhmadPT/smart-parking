from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from access.models import AccessLog, ParkingConfig
from django.db.models import Q


@login_required
def dashboard(request):
    config, _ = ParkingConfig.objects.get_or_create(
        defaults={
            'open_time': '07:00',
            'close_time': '22:00',
            'max_capacity': 50,
        }
    )
    
    today = timezone.now().date()
    today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    today_end = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))
    
    entries_today = AccessLog.objects.filter(
        event_type='ENTRY',
        timestamp__range=[today_start, today_end]
    ).count()
    
    exits_today = AccessLog.objects.filter(
        event_type='EXIT',
        timestamp__range=[today_start, today_end]
    ).count()
    
    denials_today = AccessLog.objects.filter(
        event_type='DENIED',
        timestamp__range=[today_start, today_end]
    ).count()
    
    recent_logs = AccessLog.objects.all()[:10]
    
    context = {
        'config': config,
        'recent_logs': recent_logs,
        'entries_today': entries_today,
        'exits_today': exits_today,
        'denials_today': denials_today,
        'current_count': config.current_count,
        'capacity': config.max_capacity,
        'occupancy_pct': config.occupancy_pct(),
    }
    
    return render(request, 'core/dashboard.html', context)
