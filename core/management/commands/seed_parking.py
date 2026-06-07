from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, time
import random
from vehicles.models import Vehicle, SubscriptionPlan
from access.models import ParkingConfig, AccessLog


class Command(BaseCommand):
    help = 'Seed the database with initial parking data'

    def handle(self, *args, **options):
        self.stdout.write('Starting database seeding...')
        
        config, created = ParkingConfig.objects.get_or_create(
            defaults={
                'open_time': time(7, 0),
                'close_time': time(22, 0),
                'max_capacity': 50,
                'current_count': 12,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created ParkingConfig'))
        
        plans_data = [
            ('free', 'Free', 0, 1, 0, False, 'Basic access with 1 entry per day'),
            ('basic', 'Basic', 9.99, 5, 1, False, '5 entries per day'),
            ('premium', 'Premium', 19.99, 20, 2, False, '20 entries per day'),
            ('vip', 'VIP', 49.99, 0, 3, True, 'Unlimited access with priority'),
        ]
        for name, display, price, max_entries, priority, unlimited, desc in plans_data:
            SubscriptionPlan.objects.get_or_create(
                name=name,
                defaults={
                    'display_name': display,
                    'price': price,
                    'max_entries_per_day': max_entries,
                    'priority_level': priority,
                    'has_unlimited_access': unlimited,
                    'description': desc,
                }
            )
        self.stdout.write(self.style.SUCCESS('Created subscription plans'))

        plates = [
            ('16TAC123', 'Ahmed Bennani', 'Toyota', 'White'),
            ('16TZA456', 'Fatima Zouaoui', 'Honda', 'Black'),
            ('16ALD789', 'Karim Mebarki', 'BMW', 'Silver'),
            ('16BAB012', 'Leila Saadi', 'Ford', 'Red'),
            ('16BOV345', 'Mohamed Amrani', 'Mercedes', 'Blue'),
            ('16WST678', 'Aïsha Rahmani', 'Volkswagen', 'Gray'),
            ('16OUA901', 'Hassan Djelloul', 'Peugeot', 'Green'),
            ('16CHL234', 'Nora Messi', 'Renault', 'Yellow'),
            ('16GNU567', 'Riad Yahiaoui', 'Fiat', 'Orange'),
            ('16TRZ890', 'Yasmine Bouazza', 'Hyundai', 'Brown'),
        ]
        
        plan_choices = list(SubscriptionPlan.objects.all())
        for i, (plate, owner, brand, color) in enumerate(plates):
            plan = random.choice(plan_choices) if plan_choices else None
            expires_at = timezone.now() + timedelta(days=random.randint(30, 365)) if plan and plan.name != 'free' else None
            vehicle, created = Vehicle.objects.get_or_create(
                plate_number=plate,
                defaults={
                    'owner_name': owner,
                    'owner_phone': '+213' + str(random.randint(600000000, 799999999)),
                    'owner_email': f'{owner.lower().replace(" ", ".")}@example.com',
                    'vehicle_type': random.choice(['car', 'truck', 'van']),
                    'vehicle_brand': brand,
                    'vehicle_color': color,
                    'is_registered': True,
                    'is_banned': False,
                    'subscription_plan': plan,
                    'subscription_expires_at': expires_at,
                }
            )
            if created:
                self.stdout.write(f'  Created vehicle: {plate}')
        
        banned_plates = [
            ('16DZA111', 'Banned Owner 1', 'Kia', 'Black'),
            ('16DZA222', 'Banned Owner 2', 'Skoda', 'Silver'),
        ]
        
        for plate, owner, brand, color in banned_plates:
            vehicle, created = Vehicle.objects.get_or_create(
                plate_number=plate,
                defaults={
                    'owner_name': owner,
                    'owner_phone': '+213' + str(random.randint(600000000, 799999999)),
                    'owner_email': f'{owner.lower().replace(" ", ".")}@example.com',
                    'vehicle_type': 'car',
                    'vehicle_brand': brand,
                    'vehicle_color': color,
                    'is_registered': True,
                    'is_banned': True,
                    'ban_reason': 'Unpaid parking fees',
                }
            )
            if created:
                self.stdout.write(f'  Created banned vehicle: {plate}')
        
        now = timezone.now()
        for i in range(20):
            days_ago = random.randint(0, 6)
            hours_ago = random.randint(0, 23)
            event_time = now - timedelta(days=days_ago, hours=hours_ago)
            
            event_type = random.choice(['ENTRY', 'EXIT', 'DENIED'])
            reason = ''
            if event_type == 'DENIED':
                reason = random.choice([
                    'NOT_REGISTERED',
                    'BANNED',
                    'OUTSIDE_HOURS',
                    'PARKING_FULL',
                ])
            
            vehicle = random.choice(Vehicle.objects.all())
            
            log = AccessLog.objects.create(
                vehicle=vehicle,
                plate_detected=vehicle.plate_number,
                event_type=event_type,
                denial_reason=reason,
                confidence_score=random.uniform(0.75, 0.99),
                timestamp=event_time,
                gate='MAIN',
                processed_by='AUTO',
            )
        
        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
