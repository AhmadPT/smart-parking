from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime
from access.models import AccessLog, ParkingConfig, Gate
from django.db.models import Q, Count
from collections import defaultdict
import json


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


@login_required
def analytics(request):
    config, _ = ParkingConfig.objects.get_or_create(
        defaults={
            'open_time': '07:00',
            'close_time': '22:00',
            'max_capacity': 50,
        }
    )
    
    today = timezone.now().date()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    # Hourly traffic today
    hourly_labels = []
    hourly_entries = []
    hourly_exits = []
    for h in range(24):
        hour_start = today_start + timedelta(hours=h)
        hour_end = hour_start + timedelta(hours=1)
        hourly_labels.append(f'{h:02d}:00')
        hourly_entries.append(
            AccessLog.objects.filter(event_type='ENTRY', timestamp__range=[hour_start, hour_end]).count()
        )
        hourly_exits.append(
            AccessLog.objects.filter(event_type='EXIT', timestamp__range=[hour_start, hour_end]).count()
        )
    
    # Daily traffic last 7 days
    daily_labels = []
    daily_entries = []
    daily_exits = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(day, datetime.max.time()))
        daily_labels.append(day.strftime('%a %d'))
        daily_entries.append(
            AccessLog.objects.filter(event_type='ENTRY', timestamp__range=[day_start, day_end]).count()
        )
        daily_exits.append(
            AccessLog.objects.filter(event_type='EXIT', timestamp__range=[day_start, day_end]).count()
        )
    
    # Denial reasons breakdown
    denial_data = (
        AccessLog.objects
        .filter(event_type='DENIED')
        .values('denial_reason')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    denial_labels = [d['denial_reason'] for d in denial_data]
    denial_counts = [d['total'] for d in denial_data]
    
    # Gate usage
    gate_data = (
        AccessLog.objects
        .values('gate')
        .annotate(total=Count('id'))
        .order_by('gate')
    )
    gate_labels = [g['gate'] for g in gate_data]
    gate_counts = [g['total'] for g in gate_data]
    
    context = {
        'config': config,
        'occupancy_pct': config.occupancy_pct(),
        'current_count': config.current_count,
        'capacity': config.max_capacity,
        'hourly_labels': json.dumps(hourly_labels),
        'hourly_entries': json.dumps(hourly_entries),
        'hourly_exits': json.dumps(hourly_exits),
        'daily_labels': json.dumps(daily_labels),
        'daily_entries': json.dumps(daily_entries),
        'daily_exits': json.dumps(daily_exits),
        'denial_labels': json.dumps(denial_labels),
        'denial_counts': json.dumps(denial_counts),
        'gate_labels': json.dumps(gate_labels),
        'gate_counts': json.dumps(gate_counts),
    }
    
    return render(request, 'core/analytics.html', context)
