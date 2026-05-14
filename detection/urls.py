from django.urls import path
from . import views

app_name = 'detection'

urlpatterns = [
    path('live/', views.live_view, name='live'),
    path('manual-trigger/', views.manual_trigger, name='manual_trigger'),
]
