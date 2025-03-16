from django.core.management.base import BaseCommand
from overdrive.models import Booking
from fleet_management.models import Car, Manufacturer, Owner, Vehicle
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.core.files import File

User = get_user_model()

class Command(BaseCommand):
    help = 'Insert sample data into the database'

    legazpi_geojson = '''{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "place": "city",
        "name": "Legazpi City",
        "admin_level": "8",
        "wikidata": "Q108061",
        "wikipedia": "en:Legazpi, Albay"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [123.718987, 13.192956],
            [123.770247, 13.268389],
            [123.782606, 13.280348],
            [123.794966, 13.292307],
            [123.807325, 13.304266],
            [123.819685, 13.316225],
            [123.832045, 13.328184],
            [123.844404, 13.340143],
            [123.856764, 13.352101],
            [123.869123, 13.36406],
            [123.881483, 13.376019],
            [123.893843, 13.387978],
            [123.906202, 13.399936],
            [123.918562, 13.411895],
            [123.930922, 13.423854],
            [123.943281, 13.435812],
            [123.955641, 13.447771],
            [123.968000, 13.459729],
            [123.980360, 13.471688],
            [123.992720, 13.483647],
            [124.005079, 13.495605],
            [124.017439, 13.507564],
            [124.029799, 13.519522],
            [124.042158, 13.531481],
            [124.054518, 13.543439],
            [124.066877, 13.555398],
            [124.079237, 13.567356],
            [124.091597, 13.579314],
            [124.103956, 13.591273],
            [124.116316, 13.603231],
            [124.128675, 13.61519],
            [124.141035, 13.627148],
            [124.153395, 13.639106],
            [124.165754, 13.651064],
            [124.178114, 13.663023],
            [123.718987, 13.192956]
          ]
        ]
      }
    }
  ]
}'''

    @transaction.atomic
    def handle(self, *args, **options):

        if not settings.DEBUG:
            self.stdout.write(self.style.ERROR('This command can only be run in DEBUG mode.'))
            return

        try:
            # Users data
            users = [
                {"first_name": "john_doe", "email": "john@carowner.com", "password": "password", "user_type": "car_owner"},
                {"first_name": "jane_smith", "email": "jane@customer.com", "password": "password", "user_type": "customer"},
                {"first_name": "mike_johnson", "email": "mike@carowner.com", "password": "password", "user_type": "car_owner"},
            ]
            # Insert users
            for user_data in users:
                user = User.objects.create_user(**user_data)
                user.is_verified = True
                user.is_active = True
                user.save()
            self.stdout.write(self.style.SUCCESS('Inserted users.'))

            # Owner
            owners = [
                {"name": "John Doe Rental", "user_id": 1 },
                {"name": "Mike Johnson Travel", "user_id": 3},
            ]

            # Insert owners
            for owner in owners:
                user_owner = User.objects.get(id=owner['user_id'])
                owner['user'] = user_owner
                Owner.objects.create(
                    user = owner['user'],
                    name = owner['name']
                )
            self.stdout.write(self.style.SUCCESS('Inserted owners.'))

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
                {
                    "make": 1, "model": "Corolla", 
                    "year": 2022, "is_available": True, "price_per_hour": 120.00, "license_plate": "ABC1234",
                    'image_filename': 'toyota_corolla_2022.jpg', "owner_id": 1, "passenger_capacity": 5,
                },
                {
                    "make": 2, "model": "Civic", "year": 2021, "is_available": True, "price_per_hour": 130.00, "license_plate": "CDE1234",
                    'image_filename': 'honda_civic_2021.jpg', "owner_id": 1, "passenger_capacity": 5,
                },
                {
                    "make": 3, "model": "Mustang", "year": 2023, "is_available": False, "price_per_hour": 150.00, "license_plate": "EFG1234",
                    'image_filename': 'ford_mustang_2023.jpg', "owner_id": 2, "passenger_capacity": 5,
                },
                {
                    "make": 4, "model": "Malibu", "year": 2020, "is_available": True, "price_per_hour": 300.00, "license_plate": "HIJ1234",
                    'image_filename': 'chevrolet_malibu_2020.jpg', "owner_id": 1, "passenger_capacity": 5,
                },
            ]
    
            # Insert cars
            for car in cars:
                manufacturer = Manufacturer.objects.get(id=car['make'])
                car['make'] = manufacturer
                owner = Owner.objects.get(id=car['owner_id'])
                car['owner'] = owner
                car['name'] = owner.name
                image_filename = car['image_filename']
                car_obj = Car.objects.create(
                    license_plate=car['license_plate'],
                    passenger_capacity=car['passenger_capacity'],
                    make=car['make'],
                    model=car['model'],
                    year=car['year'],
                    price_per_hour=car['price_per_hour'],
                    location=self.legazpi_geojson,
                    is_available=car['is_available'],
                    owner=car['owner'],
                    name=car['name'],
                )
                image_path = f'{settings.BASE_DIR}/overdrive/sample_data/cars_images/{image_filename}' # Adjust path if needed
                print(image_path)
                with open(image_path, 'rb') as image_file:
                    car_obj.image.save(image_filename, File(image_file), save=False) # save=False for now
                    car_obj.save() # Now save to trigger file storage
            
            self.stdout.write(self.style.SUCCESS('Inserted cars.'))
            
            # Bookings data
            bookings = [
                {"vehicle": 3, "start_time": timezone.make_aware(datetime(2025, 2, 10, 8, 0)),
                 "end_time": timezone.make_aware(datetime(2025, 2, 15, 18, 0)), "user": 2, "total_price": 1200},
                {"vehicle": 1, "start_time": timezone.make_aware(datetime(2025, 2, 17, 9, 0)),
                 "end_time": timezone.make_aware(datetime(2025, 2, 20, 17, 0)), "user": 2, "total_price": 1200},
                {"vehicle": 2, "start_time": timezone.make_aware(datetime(2025, 2, 25, 10, 0)),
                 "end_time": timezone.make_aware(datetime(2025, 3, 1, 16, 0)), "user": 2, "total_price": 1200},
            ]
            # Insert bookings
            for booking in bookings:
                # Assuming car_id is a foreign key to Car model
                vehicle = Vehicle.objects.get(id=booking['vehicle'])
                booking_user = User.objects.get(id=booking['user'])
                Booking.objects.create(vehicle=vehicle, start_time=booking['start_time'], end_time=booking['end_time'], 
                                       user=booking_user, total_price=booking['total_price'])
            self.stdout.write(self.style.SUCCESS('Inserted bookings.'))
            # Output success message
            self.stdout.write(self.style.SUCCESS('Successfully inserted sample data'))
            
        except Exception as e:
            # Transaction will rollback automatically on any exception
            self.stdout.write(self.style.ERROR(f'Error inserting sample data: {str(e)}'))
