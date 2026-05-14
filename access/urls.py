from django.urls import path
from . import views

app_name = 'access'

urlpatterns = [
    path('logs/', views.access_logs, name='logs'),
    path('export/', views.export_logs_csv, name='export'),
    path('config/', views.parking_config, name='config'),
    path('toggle-override/', views.toggle_override, name='toggle_override'),
    path('reset-count/', views.reset_count, name='reset_count'),
]
