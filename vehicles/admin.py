from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'plate_number',
        'owner_name',
        'vehicle_type',
        'is_registered',
        'is_banned',
        'registered_at',
    )
    list_filter = (
        'vehicle_type',
        'is_registered',
        'is_banned',
        'registered_at',
    )
    search_fields = (
        'plate_number',
        'owner_name',
        'owner_phone',
        'owner_email',
    )
    list_editable = (
        'is_banned',
        'is_registered',
    )
    readonly_fields = (
        'registered_at',
        'updated_at',
    )
    fieldsets = (
        ('Vehicle Information', {
            'fields': (
                'plate_number',
                'vehicle_type',
                'vehicle_brand',
                'vehicle_color',
                'photo',
            )
        }),
        ('Owner Information', {
            'fields': (
                'owner_name',
                'owner_phone',
                'owner_email',
            )
        }),
        ('Status', {
            'fields': (
                'is_registered',
                'is_banned',
                'ban_reason',
            )
        }),
        ('Metadata', {
            'fields': (
                'registered_at',
                'updated_at',
                'notes',
            )
        }),
    )
