from django import forms
from .models import ParkingConfig


class ParkingConfigForm(forms.ModelForm):
    class Meta:
        model = ParkingConfig
        fields = [
            'open_time',
            'close_time',
            'max_capacity',
        ]
        widgets = {
            'open_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                }
            ),
            'close_time': forms.TimeInput(
                attrs={
                    'type': 'time',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                }
            ),
            'max_capacity': forms.NumberInput(
                attrs={
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                    'min': '1',
                }
            ),
        }
