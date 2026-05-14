from django.db import models
from django.core.validators import RegexValidator


class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('car', 'Car'),
        ('truck', 'Truck'),
        ('motorcycle', 'Motorcycle'),
        ('van', 'Van'),
    ]
    
    plate_number = models.CharField(
        max_length=20,
        unique=True,
        help_text='e.g., 16TAC123'
    )
    owner_name = models.CharField(max_length=100)
    owner_phone = models.CharField(max_length=20, blank=True)
    owner_email = models.EmailField(blank=True)
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPES,
        default='car'
    )
    vehicle_brand = models.CharField(max_length=50, blank=True)
    vehicle_color = models.CharField(max_length=30, blank=True)
    is_registered = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True)
    photo = models.ImageField(
        upload_to='vehicles/',
        blank=True,
        null=True
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-registered_at']
        indexes = [
            models.Index(fields=['plate_number']),
            models.Index(fields=['is_banned']),
        ]

    def __str__(self):
        return self.plate_number

    def is_allowed(self):
        return self.is_registered and not self.is_banned
