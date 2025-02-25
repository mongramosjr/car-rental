from rest_framework import serializers
from .models import Car, Manufacturer
from django.core.exceptions import ValidationError

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ['id', 'name', 'country']

class CarSerializer(serializers.ModelSerializer):
    make = ManufacturerSerializer(read_only=True)
    make_id = serializers.PrimaryKeyRelatedField(
        queryset=Manufacturer.objects.all(),
        source='make',
        write_only=True
    )

    class Meta:
        model = Car
        fields = ['id', 'license_plate', 'make', 'make_id', 'model', 'year',
                 'price_per_hour', 'location', 'is_available', 'owner']
        read_only_fields = ['owner']  # Owner will be set automatically

    def validate(self, data):
        # Additional validation if needed
        if data['price_per_hour'] <= 0:
            raise ValidationError("Price per hour must be greater than 0")
        return data
