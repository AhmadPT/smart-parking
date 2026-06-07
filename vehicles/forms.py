from django import forms
from .models import Vehicle, SubscriptionPlan


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'plate_number',
            'owner_name',
            'owner_phone',
            'owner_email',
            'vehicle_type',
            'vehicle_brand',
            'vehicle_color',
            'is_registered',
            'is_banned',
            'ban_reason',
            'subscription_plan',
            'subscription_expires_at',
            'photo',
            'notes',
        ]
        widgets = {
            'plate_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '16TAC123',
                'style': 'text-transform: uppercase;'
            }),
            'owner_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Owner name',
            }),
            'owner_phone': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '+213...',
            }),
            'owner_email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'email@example.com',
            }),
            'vehicle_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'vehicle_brand': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Toyota',
            }),
            'vehicle_color': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'White',
            }),
            'is_registered': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4',
            }),
            'is_banned': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4',
            }),
            'ban_reason': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Reason for ban',
                'rows': 3,
            }),
            'subscription_plan': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'subscription_expires_at': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            }),
            'photo': forms.FileInput(attrs={
                'class': 'w-full',
                'accept': 'image/*',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Additional notes',
                'rows': 3,
            }),
        }
