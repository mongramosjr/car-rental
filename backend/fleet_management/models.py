from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime
from django.utils import timezone

User = get_user_model()
current_year = datetime.datetime.now().year

class Manufacturer(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Owner(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Vehicle(models.Model):
    name = models.CharField(max_length=100, help_text="Name of vehicle")
    owner = models.ForeignKey(Owner, on_delete=models.SET_NULL, null=True, blank=True)
    passenger_capacity = models.PositiveSmallIntegerField()
    is_available = models.BooleanField(default=True)
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    location = models.JSONField(blank=True, null=True)
    image = models.ImageField(upload_to='cars/', blank=True, null=True, help_text="Image of vehicle")

    def __str__(self):
        return f"{self.name} ({self.__class__.__name__})"

class Car(Vehicle):  # Separate table for Cars
    license_plate = models.CharField(max_length=20, unique=True)
    make = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)
    model = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1978),
            MaxValueValidator(current_year)
        ],
        help_text=f'Enter a year between 1978 and {current_year}'
    )
    fuel_type = models.CharField(max_length=50, choices=[("gasoline", "Gasoline"), ("diesel", "Diesel"), ("electric", "Electric")])

    def __str__(self):
        return f"{self.make.name} {self.model} {self.year}"

class MotorizedBanca(Vehicle):  # Separate table for Banca
    vessel_official_number = models.CharField(max_length=64, unique=True)

class PassengerVessel(Vehicle):  # Separate table for Vessels
    vessel_official_number = models.CharField(max_length=64, unique=True)
    gross_tonnage = models.FloatField(help_text="Gross tonnage")
    net_tonnage = models.FloatField(help_text="Net tonnage")
