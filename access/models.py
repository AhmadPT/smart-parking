from django.db import models
from django.contrib.auth.models import User
from datetime import time


class Zone(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    max_capacity = models.IntegerField(default=50)
    current_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def is_full(self):
        return self.current_count >= self.max_capacity

    def occupancy_pct(self):
        if self.max_capacity == 0:
            return 0
        return round((self.current_count / self.max_capacity) * 100)

    def gates_list(self):
        return self.gates.all()


class Gate(models.Model):
    DIRECTION_CHOICES = [
        ('ENTRANCE', 'Entrance'),
        ('EXIT', 'Exit'),
    ]

    zone = models.ForeignKey(
        Zone, on_delete=models.CASCADE,
        related_name='gates'
    )
    name = models.CharField(max_length=50)
    direction = models.CharField(
        max_length=10, choices=DIRECTION_CHOICES,
        default='ENTRANCE'
    )
    camera_ip = models.GenericIPAddressField(
        blank=True, null=True,
        help_text='IP address of the camera (e.g., 192.168.1.100)'
    )
    camera_port = models.IntegerField(default=554)
    camera_username = models.CharField(max_length=100, blank=True)
    camera_password = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    open_time = models.TimeField(default='07:00')
    close_time = models.TimeField(default='22:00')
    allowed_vehicle_types = models.CharField(
        max_length=200, blank=True,
        help_text='Comma-separated vehicle types allowed (leave blank for all)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['zone__name', 'name']
        unique_together = ['zone', 'name']

    def __str__(self):
        return f"{self.zone.name} - {self.name} ({self.get_direction_display()})"

    def is_within_hours(self):
        from datetime import datetime
        now = datetime.now().time()
        return self.open_time <= now <= self.close_time

    def allows_vehicle_type(self, vehicle_type):
        if not self.allowed_vehicle_types:
            return True
        allowed = [t.strip().lower() for t in self.allowed_vehicle_types.split(',')]
        return vehicle_type.lower() in allowed

    def rtsp_url(self):
        if not self.camera_ip:
            return None
        if self.camera_username:
            return f'rtsp://{self.camera_username}:{self.camera_password}@{self.camera_ip}:{self.camera_port}/'
        return f'rtsp://{self.camera_ip}:{self.camera_port}/'


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
        ('SUBSCRIPTION_EXPIRED', 'Subscription expired'),
        ('DAILY_LIMIT_REACHED', 'Daily entry limit reached'),
        ('VEHICLE_TYPE_NOT_ALLOWED', 'Vehicle type not allowed at this gate'),
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
    zone = models.ForeignKey(
        Zone, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='access_logs'
    )
    processed_by = models.CharField(max_length=20, default='AUTO')

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['plate_detected']),
        ]

    def __str__(self):
        return f"{self.event_type} {self.plate_detected} @ {self.timestamp}"
