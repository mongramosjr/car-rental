from rest_framework import serializers
from .models import Car, Manufacturer, Owner
from django.core.exceptions import ValidationError

class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ['id', 'name', 'country']

class OwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = ['id', 'name']

class CarSerializer(serializers.ModelSerializer):
    make = ManufacturerSerializer(read_only=True)
    make_id = serializers.PrimaryKeyRelatedField(
        queryset=Manufacturer.objects.all(),
        source='make',
        write_only=True
    )

    owner = OwnerSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=Owner.objects.all(),
        source='owner',
        write_only=True
    )

    image_url = serializers.SerializerMethodField() # Add this field
    vehicle_id = serializers.IntegerField(source='vehicle_ptr_id', read_only=True)


    class Meta:
        model = Car
        fields = ['id', 'vehicle_id', 'license_plate', 'passenger_capacity', 'make', 'make_id', 'model', 'year',
                 'price_per_hour', 'location', 'is_available', 'owner', 'owner_id', 'image_url']
        read_only_fields = ['image_url', 'vehicle_id']

    def validate(self, data):
        # Additional validation if needed
        if data['price_per_hour'] <= 0:
            raise ValidationError("Price per hour must be greater than 0")
        return data

    def get_image_url(self, car): # Method to generate image URL
        if car.image:
            request = self.context.get('request') # Get request from context
            if request:
                return request.build_absolute_uri(car.image.url) # Build full URL
        return None # Or return a default image URL or empty string
