from rest_framework import serializers
from .models import Booking
from fleet_management.models import Vehicle
from django.contrib.auth import get_user_model

User = get_user_model()


class VehicleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vehicle
        fields = ['id', 'name', 'passenger_capacity', 'price_per_hour', 'location', 'is_available']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'first_name', 'last_name']

class BookingSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    status = serializers.CharField(read_only=True)

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )

    vehicle = VehicleSerializer(read_only=True)
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(),
        source='vehicle',
        write_only=True
    )
    
    class Meta:
        model = Booking
        fields = ['id', 'user', 'user_id', 'vehicle', 'vehicle_id', 'start_time', 'end_time', 'total_price', 'status']
