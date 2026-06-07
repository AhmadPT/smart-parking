from django.urls import path
from . import views

app_name = 'access'

urlpatterns = [
    path('logs/', views.access_logs, name='logs'),
    path('export/', views.export_logs_csv, name='export'),
    path('config/', views.parking_config, name='config'),
    path('toggle-override/', views.toggle_override, name='toggle_override'),
    path('reset-count/', views.reset_count, name='reset_count'),
    path('zones/', views.zone_list, name='zones'),
    path('zones/add/', views.zone_add, name='zone_add'),
    path('zones/<int:pk>/edit/', views.zone_edit, name='zone_edit'),
    path('zones/<int:pk>/delete/', views.zone_delete, name='zone_delete'),
    path('gates/', views.gate_list, name='gates'),
    path('gates/add/', views.gate_add, name='gate_add'),
    path('gates/<int:pk>/edit/', views.gate_edit, name='gate_edit'),
    path('gates/<int:pk>/delete/', views.gate_delete, name='gate_delete'),
]
