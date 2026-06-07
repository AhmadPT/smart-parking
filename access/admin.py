from django.contrib import admin
from .models import AccessLog, ParkingConfig, Zone, Gate


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = (
        'plate_detected',
        'event_type',
        'denial_reason',
        'confidence_score',
        'timestamp',
        'gate',
    )
    list_filter = (
        'event_type',
        'denial_reason',
        'gate',
        'timestamp',
    )
    search_fields = (
        'plate_detected',
        'vehicle__owner_name',
    )
    date_hierarchy = 'timestamp'
    readonly_fields = (
        'timestamp',
        'processed_by',
    )
    fieldsets = (
        ('Detection', {
            'fields': (
                'plate_detected',
                'confidence_score',
            )
        }),
        ('Event', {
            'fields': (
                'event_type',
                'denial_reason',
            )
        }),
        ('Vehicle', {
            'fields': (
                'vehicle',
            )
        }),
        ('Media', {
            'fields': (
                'snapshot',
            )
        }),
        ('Metadata', {
            'fields': (
                'timestamp',
                'gate',
                'processed_by',
            )
        }),
    )


@admin.register(ParkingConfig)
class ParkingConfigAdmin(admin.ModelAdmin):
    list_display = (
        'open_time',
        'close_time',
        'max_capacity',
        'current_count',
        'is_manual_open',
        'is_manual_closed',
    )
    readonly_fields = (
        'updated_at',
        'updated_by',
    )
    fieldsets = (
        ('Operating Hours', {
            'fields': (
                'open_time',
                'close_time',
            )
        }),
        ('Capacity', {
            'fields': (
                'max_capacity',
                'current_count',
            )
        }),
        ('Manual Override', {
            'fields': (
                'is_manual_open',
                'is_manual_closed',
            )
        }),
        ('Metadata', {
            'fields': (
                'updated_at',
                'updated_by',
            )
        }),
    )


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'is_active', 'current_count', 'max_capacity', 'occupancy_pct')
    list_filter = ('is_active',)
    search_fields = ('name', 'location')


class GateInline(admin.TabularInline):
    model = Gate
    extra = 0


@admin.register(Gate)
class GateAdmin(admin.ModelAdmin):
    list_display = ('name', 'zone', 'direction', 'camera_ip', 'is_active')
    list_filter = ('zone', 'direction', 'is_active')
    search_fields = ('name', 'camera_ip')
