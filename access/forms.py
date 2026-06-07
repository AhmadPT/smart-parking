from django import forms
from .models import ParkingConfig, Zone, Gate


class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ['name', 'location', 'is_active', 'max_capacity', 'current_count']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g., Zone 1',
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'max_capacity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '1',
            }),
            'current_count': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4'}),
        }


class GateForm(forms.ModelForm):
    class Meta:
        model = Gate
        fields = [
            'zone', 'name', 'direction',
            'camera_ip', 'camera_port', 'camera_username', 'camera_password',
            'is_active', 'open_time', 'close_time',
            'allowed_vehicle_types',
        ]
        widgets = {
            'zone': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g., Entrance Gate',
            }),
            'direction': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'camera_ip': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '192.168.1.100',
            }),
            'camera_port': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'camera_username': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'admin',
            }),
            'camera_password': forms.PasswordInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'camera password',
            }),
            'open_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'close_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'allowed_vehicle_types': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'car, truck, motorcycle (leave blank for all)',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4'}),
        }


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
