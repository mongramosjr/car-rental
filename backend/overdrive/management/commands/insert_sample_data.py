from django.core.management.base import BaseCommand
from overdrive.models import Booking
from fleet_management.models import Car, Manufacturer
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Insert sample data into the database'

    @transaction.atomic
    def handle(self, *args, **options):

        if not settings.DEBUG:
            self.stdout.write(self.style.ERROR('This command can only be run in DEBUG mode.'))
            return

        try:
            # Users data
            users = [
                {"first_name": "john_doe", "email": "john@example.com", "password": "password"},
                {"first_name": "jane_smith", "email": "jane@example.com", "password": "password"},
                {"first_name": "mike_johnson", "email": "mike@example.com", "password": "password"},
            ]
            # Insert users
            for user_data in users:
                User.objects.create_user(**user_data)
            self.stdout.write(self.style.SUCCESS('Inserted users.'))

            # Manufacturer data
            manufacturers = [
                {"name": "Toyota", "country": "Philippines"},
                {"name": "Honda", "country": "Philippines"},
                {"name": "Ford", "country": "Philippines"},
                {"name": "Chevrolet", "country": "Philippines"},
            ]
    
            # Insert cars
            for manufacturer in manufacturers:
                Manufacturer.objects.create(**manufacturer)
            self.stdout.write(self.style.SUCCESS('Inserted manufacturers.'))
            
            # Cars data
            cars = [
                {"make": 1, "model": "Corolla", "year": 2022, "is_available": True, "price_per_hour": 120.00, "license_plate": "ABC1234", "passenger_capacity": 5,},
                {"make": 2, "model": "Civic", "year": 2021, "is_available": True, "price_per_hour": 130.00, "license_plate": "CDE1234", "passenger_capacity": 5,},
                {"make": 3, "model": "Mustang", "year": 2023, "is_available": False, "price_per_hour": 150.00, "license_plate": "EFG1234", "passenger_capacity": 5,},
                {"make": 4, "model": "Malibu", "year": 2020, "is_available": True, "price_per_hour": 300.00, "license_plate": "HIJ1234", "passenger_capacity": 5,},
            ]
    
            # Insert cars
            for car in cars:
                manufacturer = Manufacturer.objects.get(id=car['make'])
                car['make'] = manufacturer
                Car.objects.create(**car)
            self.stdout.write(self.style.SUCCESS('Inserted cars.'))
            
            # Bookings data
            bookings = [
                {"car": 3, "start_time": timezone.make_aware(datetime(2025, 2, 10, 8, 0)),
                 "end_time": timezone.make_aware(datetime(2025, 2, 15, 18, 0)), "user": 1, "total_price": 1200},
                {"car": 1, "start_time": timezone.make_aware(datetime(2025, 2, 17, 9, 0)),
                 "end_time": timezone.make_aware(datetime(2025, 2, 20, 17, 0)), "user": 2, "total_price": 1200},
                {"car": 2, "start_time": timezone.make_aware(datetime(2025, 2, 25, 10, 0)),
                 "end_time": timezone.make_aware(datetime(2025, 3, 1, 16, 0)), "user": 3, "total_price": 1200},
            ]
            # Insert bookings
            for booking in bookings:
                # Assuming car_id is a foreign key to Car model
                car = Car.objects.get(id=booking['car'])
                booking_user = User.objects.get(id=booking['user'])
                Booking.objects.create(car=car, start_time=booking['start_time'], end_time=booking['end_time'], 
                                       user=booking_user, total_price=booking['total_price'])
            self.stdout.write(self.style.SUCCESS('Inserted bookings.'))
            # Output success message
            self.stdout.write(self.style.SUCCESS('Successfully inserted sample data'))
            
        except Exception as e:
            # Transaction will rollback automatically on any exception
            self.stdout.write(self.style.ERROR(f'Error inserting sample data: {str(e)}'))
