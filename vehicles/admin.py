from django.contrib import admin
from .models import Vehicle, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'display_name',
        'price',
        'max_entries_per_day',
        'priority_level',
        'has_unlimited_access',
        'is_active',
    )
    list_editable = (
        'max_entries_per_day',
        'priority_level',
        'has_unlimited_access',
        'is_active',
    )


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'plate_number',
        'owner_name',
        'vehicle_type',
        'subscription_plan',
        'is_subscription_active',
        'is_registered',
        'is_banned',
        'registered_at',
    )
    list_filter = (
        'vehicle_type',
        'is_registered',
        'is_banned',
        'subscription_plan',
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
        ('Subscription', {
            'fields': (
                'subscription_plan',
                'subscription_expires_at',
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
