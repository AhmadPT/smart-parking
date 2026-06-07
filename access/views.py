from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from functools import wraps
from .models import AccessLog, ParkingConfig, Zone, Gate
from .forms import ParkingConfigForm, ZoneForm, GateForm
from .logic import process_exit

# Custom decorator for staff members since Django 6.0+ removed staff_member_required
def staff_member_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('admin:login')
        return view_func(request, *args, **kwargs)
    return wrapped_view


@login_required
def access_logs(request):
    logs = AccessLog.objects.all()
    
    date_from = request.GET.get('date_from')
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=date_from_obj)
        except ValueError:
            pass
    
    date_to = request.GET.get('date_to')
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            logs = logs.filter(timestamp__lte=date_to_obj)
        except ValueError:
            pass
    
    event_type = request.GET.get('event_type')
    if event_type:
        logs = logs.filter(event_type=event_type)
    
    plate_search = request.GET.get('plate')
    if plate_search:
        logs = logs.filter(plate_detected__icontains=plate_search)
    
    reason = request.GET.get('reason')
    if reason:
        logs = logs.filter(denial_reason=reason)
    
    paginator = Paginator(logs, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_count = logs.count()
    entries_count = logs.filter(event_type='ENTRY').count()
    exits_count = logs.filter(event_type='EXIT').count()
    denials_count = logs.filter(event_type='DENIED').count()
    
    context = {
        'page_obj': page_obj,
        'total_count': total_count,
        'entries_count': entries_count,
        'exits_count': exits_count,
        'denials_count': denials_count,
        'date_from': date_from,
        'date_to': date_to,
        'selected_event_type': event_type,
        'plate_search': plate_search,
        'selected_reason': reason,
    }
    
    return render(request, 'access/logs.html', context)


@login_required
def export_logs_csv(request):
    logs = AccessLog.objects.all()
    
    date_from = request.GET.get('date_from')
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=date_from_obj)
        except ValueError:
            pass
    
    date_to = request.GET.get('date_to')
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            logs = logs.filter(timestamp__lte=date_to_obj)
        except ValueError:
            pass
    
    event_type = request.GET.get('event_type')
    if event_type:
        logs = logs.filter(event_type=event_type)
    
    plate_search = request.GET.get('plate')
    if plate_search:
        logs = logs.filter(plate_detected__icontains=plate_search)
    
    reason = request.GET.get('reason')
    if reason:
        logs = logs.filter(denial_reason=reason)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="parking_log_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Timestamp',
        'Plate Detected',
        'Event Type',
        'Denial Reason',
        'Confidence Score',
        'Owner Name',
        'Gate',
        'Processed By',
    ])
    
    for log in logs:
        owner_name = log.vehicle.owner_name if log.vehicle else 'Unknown'
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.plate_detected,
            log.get_event_type_display(),
            log.get_denial_reason_display(),
            f'{log.confidence_score:.2f}',
            owner_name,
            log.gate,
            log.processed_by,
        ])
    
    return response


@login_required
@staff_member_required
def parking_config(request):
    config, _ = ParkingConfig.objects.get_or_create(
        defaults={
            'open_time': '07:00',
            'close_time': '22:00',
            'max_capacity': 50,
        }
    )
    
    if request.method == 'POST':
        form = ParkingConfigForm(request.POST, instance=config)
        if form.is_valid():
            config = form.save(commit=False)
            config.updated_by = request.user
            config.save()
            return redirect('access:config')
    else:
        form = ParkingConfigForm(instance=config)
    
    context = {
        'form': form,
        'config': config,
    }
    return render(request, 'access/config.html', context)


@login_required
@staff_member_required
@require_http_methods(['POST'])
def toggle_override(request):
    config, _ = ParkingConfig.objects.get_or_create(
        defaults={
            'open_time': '07:00',
            'close_time': '22:00',
            'max_capacity': 50,
        }
    )
    
    action = request.POST.get('action', 'auto')
    
    if action == 'open':
        config.is_manual_open = True
        config.is_manual_closed = False
    elif action == 'close':
        config.is_manual_closed = True
        config.is_manual_open = False
    else:
        config.is_manual_open = False
        config.is_manual_closed = False
    
    config.updated_by = request.user
    config.save()
    
    if config.is_manual_closed:
        status = 'CLOSED'
    elif config.is_manual_open:
        status = 'OPEN'
    elif config.is_within_hours():
        status = 'OPEN'
    else:
        status = 'CLOSED'
    
    return JsonResponse({
        'status': status,
        'message': f'Parking lot status updated to {status}',
        'is_full': config.is_full(),
        'occupancy': config.occupancy_pct(),
    })


@login_required
@staff_member_required
@require_http_methods(['POST'])
def reset_count(request):
    config, _ = ParkingConfig.objects.get_or_create(
        defaults={
            'open_time': '07:00',
            'close_time': '22:00',
            'max_capacity': 50,
        }
    )
    
    config.current_count = 0
    config.updated_by = request.user
    config.save()
    
    return JsonResponse({
        'count': config.current_count,
        'message': 'Parking count reset to 0',
    })


@login_required
@staff_member_required
def zone_list(request):
    zones = Zone.objects.all()
    return render(request, 'access/zones.html', {'zones': zones})


@login_required
@staff_member_required
def zone_add(request):
    if request.method == 'POST':
        form = ZoneForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('access:zones')
    else:
        form = ZoneForm()
    return render(request, 'access/zone_form.html', {'form': form, 'title': 'Add Zone'})


@login_required
@staff_member_required
def zone_edit(request, pk):
    zone = get_object_or_404(Zone, pk=pk)
    if request.method == 'POST':
        form = ZoneForm(request.POST, instance=zone)
        if form.is_valid():
            form.save()
            return redirect('access:zones')
    else:
        form = ZoneForm(instance=zone)
    return render(request, 'access/zone_form.html', {'form': form, 'title': 'Edit Zone', 'zone': zone})


@login_required
@staff_member_required
@require_http_methods(['POST'])
def zone_delete(request, pk):
    zone = get_object_or_404(Zone, pk=pk)
    if zone.gates.exists():
        return JsonResponse({'error': 'Cannot delete zone with active gates'}, status=400)
    zone.delete()
    return redirect('access:zones')


@login_required
@staff_member_required
def gate_list(request):
    gates = Gate.objects.select_related('zone').all()
    return render(request, 'access/gates.html', {'gates': gates})


@login_required
@staff_member_required
def gate_add(request):
    if request.method == 'POST':
        form = GateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('access:gates')
    else:
        form = GateForm()
    return render(request, 'access/gate_form.html', {'form': form, 'title': 'Add Gate'})


@login_required
@staff_member_required
def gate_edit(request, pk):
    gate = get_object_or_404(Gate, pk=pk)
    if request.method == 'POST':
        form = GateForm(request.POST, instance=gate)
        if form.is_valid():
            form.save()
            return redirect('access:gates')
    else:
        form = GateForm(instance=gate)
    return render(request, 'access/gate_form.html', {'form': form, 'title': 'Edit Gate', 'gate': gate})


@login_required
@staff_member_required
@require_http_methods(['POST'])
def gate_delete(request, pk):
    gate = get_object_or_404(Gate, pk=pk)
    gate.delete()
    return redirect('access:gates')
