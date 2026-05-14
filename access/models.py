from django.db import models
from django.contrib.auth.models import User
from datetime import time


class ParkingConfig(models.Model):
    open_time = models.TimeField(default='07:00')
    close_time = models.TimeField(default='22:00')
    max_capacity = models.IntegerField(default=50)
    current_count = models.IntegerField(default=0)
    is_manual_open = models.BooleanField(default=False)
    is_manual_closed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = 'Parking Configuration'
        verbose_name_plural = 'Parking Configuration'

    def __str__(self):
        return 'Parking Configuration'

    def is_within_hours(self):
        from datetime import datetime
        now = datetime.now().time()
        return self.open_time <= now <= self.close_time

    def is_full(self):
        return self.current_count >= self.max_capacity

    def occupancy_pct(self):
        if self.max_capacity == 0:
            return 0
        return round((self.current_count / self.max_capacity) * 100)


class AccessLog(models.Model):
    EVENT_TYPES = [
        ('ENTRY', 'Entry'),
        ('EXIT', 'Exit'),
        ('DENIED', 'Denied'),
    ]
    
    DENIAL_REASONS = [
        ('NOT_REGISTERED', 'Not registered'),
        ('BANNED', 'Vehicle banned'),
        ('OUTSIDE_HOURS', 'Outside operating hours'),
        ('PARKING_FULL', 'Parking full'),
        ('LOW_CONFIDENCE', 'Low OCR confidence'),
        ('MANUAL_CLOSED', 'Manually closed'),
        ('UNKNOWN', 'Unknown'),
    ]
    
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    plate_detected = models.CharField(max_length=20)
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    denial_reason = models.CharField(
        max_length=30,
        choices=DENIAL_REASONS,
        blank=True
    )
    confidence_score = models.FloatField(default=0.0)
    snapshot = models.ImageField(
        upload_to='snapshots/%Y/%m/%d/',
        blank=True,
        null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    gate = models.CharField(max_length=20, default='MAIN')
    processed_by = models.CharField(max_length=20, default='AUTO')

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['plate_detected']),
        ]

    def __str__(self):
        return f"{self.event_type} {self.plate_detected} @ {self.timestamp}"
