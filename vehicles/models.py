from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class SubscriptionPlan(models.Model):
    TIERS = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('vip', 'VIP'),
    ]

    name = models.CharField(max_length=20, choices=TIERS, unique=True)
    display_name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_entries_per_day = models.IntegerField(default=1, help_text='0 = unlimited')
    priority_level = models.IntegerField(default=0, help_text='Higher = more priority')
    has_unlimited_access = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['priority_level']

    def __str__(self):
        return self.display_name


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
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicles'
    )
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
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

    def is_subscription_active(self):
        if not self.subscription_plan:
            return False
        if self.subscription_plan.has_unlimited_access:
            return True
        if self.subscription_expires_at and self.subscription_expires_at > timezone.now():
            return True
        return False

    def entries_today(self):
        from access.models import AccessLog
        today = timezone.now().date()
        return AccessLog.objects.filter(
            vehicle=self,
            event_type='ENTRY',
            timestamp__date=today
        ).count()

    def can_enter_today(self):
        if not self.is_subscription_active():
            return False
        plan = self.subscription_plan
        if plan.max_entries_per_day == 0:
            return True
        return self.entries_today() < plan.max_entries_per_day
