from django.urls import path
from .consumers import ParkingConsumer

websocket_urlpatterns = [
    path('ws/detection/', ParkingConsumer.as_asgi()),
]
