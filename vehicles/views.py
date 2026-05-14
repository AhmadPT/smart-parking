from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Vehicle
from .forms import VehicleForm
from access.models import AccessLog


@login_required
def vehicle_list(request):
    vehicles = Vehicle.objects.all()
    
    q = request.GET.get('q', '')
    if q:
        vehicles = vehicles.filter(
            models.Q(plate_number__icontains=q) |
            models.Q(owner_name__icontains=q) |
            models.Q(owner_phone__icontains=q)
        )
    
    vehicle_type = request.GET.get('type', '')
    if vehicle_type:
        vehicles = vehicles.filter(vehicle_type=vehicle_type)
    
    status = request.GET.get('status', '')
    if status == 'banned':
        vehicles = vehicles.filter(is_banned=True)
    elif status == 'unregistered':
        vehicles = vehicles.filter(is_registered=False)
    elif status == 'registered':
        vehicles = vehicles.filter(is_registered=True, is_banned=False)
    
    paginator = Paginator(vehicles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'q': q,
        'selected_type': vehicle_type,
        'selected_status': status,
    }
    return render(request, 'vehicles/list.html', context)


@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    logs = AccessLog.objects.filter(vehicle=vehicle)[:20]
    
    context = {
        'vehicle': vehicle,
        'logs': logs,
    }
    return render(request, 'vehicles/detail.html', context)


@login_required
def vehicle_add(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES)
        if form.is_valid():
            vehicle = form.save()
            return redirect('vehicles:detail', pk=vehicle.pk)
    else:
        form = VehicleForm()
    
    context = {'form': form}
    return render(request, 'vehicles/add.html', context)


@login_required
def vehicle_edit(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES, instance=vehicle)
        if form.is_valid():
            form.save()
            return redirect('vehicles:detail', pk=vehicle.pk)
    else:
        form = VehicleForm(instance=vehicle)
    
    context = {'form': form, 'vehicle': vehicle}
    return render(request, 'vehicles/edit.html', context)


@login_required
@require_http_methods(['POST'])
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        vehicle.delete()
        return redirect('vehicles:list')


@login_required
@require_http_methods(['POST'])
def vehicle_toggle_ban(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    vehicle.is_banned = not vehicle.is_banned
    ban_reason = request.POST.get('ban_reason', '')
    if ban_reason:
        vehicle.ban_reason = ban_reason
    vehicle.save()
    
    return JsonResponse({
        'banned': vehicle.is_banned,
        'plate': vehicle.plate_number,
        'message': 'Vehicle updated successfully'
    })


from django.db import models
