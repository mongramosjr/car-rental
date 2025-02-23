from rest_framework import serializers
from .models import BookingPayment
from django.conf import settings

class BookingPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingPayment
        fields = ['id', 'booking', 'amount', 'method', 'transaction_id', 'status', 'created_at']
        read_only_fields = ['id', 'transaction_id', 'status', 'created_at']
        
    def validate_method(self, value):
        if value not in dict(settings.PAYMENT_METHOD_CHOICES).keys():
            raise serializers.ValidationError("Invalid payment method.")
        return value
