from rest_framework import serializers
from .models import Booking

class BookingSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'user', 'car', 'start_time', 'end_time', 'total_price']
