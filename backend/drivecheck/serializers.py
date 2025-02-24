from rest_framework import serializers
from .models import UserVerification
from django.core.files.uploadedfile import InMemoryUploadedFile
import io

class SelfieUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVerification
        fields = ['selfie_image']
        
    def validate(self, data):
        if not data.get('selfie_image'):
            raise serializers.ValidationError("Selfie image is required")
        return data

    def update(self, instance, validated_data):
        selfie_image = validated_data.get('selfie_image')
        if selfie_image:
            encrypted_image = instance.encrypt_image(selfie_image)
            validated_data['selfie_image'] = encrypted_image
        return super().update(instance, validated_data)

class IDCardUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVerification
        fields = ['id_card_image']
        
    def validate(self, data):
        verification = self.context['verification']
        if verification.status != 'selfie_uploaded':
            raise serializers.ValidationError(
                "Please upload selfie first before ID card"
            )
        if not data.get('id_card_image'):
            raise serializers.ValidationError("ID card image is required")
        return data

    def update(self, instance, validated_data):
        id_card_image = validated_data.get('id_card_image')
        if id_card_image:
            encrypted_image = instance.encrypt_image(id_card_image)
            validated_data['id_card_image'] = encrypted_image
        return super().update(instance, validated_data)

class SelfieWithIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVerification
        fields = ['selfie_with_id_image']
        
    def validate(self, data):
        verification = self.context['verification']
        if verification.status != 'id_uploaded':
            raise serializers.ValidationError(
                "Please upload ID card first before selfie with ID"
            )
        if not data.get('selfie_with_id_image'):
            raise serializers.ValidationError("Selfie with ID image is required")
        return data

    def update(self, instance, validated_data):
        selfie_with_id_image = validated_data.get('selfie_with_id_image')
        if selfie_with_id_image:
            encrypted_image = instance.encrypt_image(selfie_with_id_image)
            validated_data['selfie_with_id_image'] = encrypted_image
        return super().update(instance, validated_data)

class VerificationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserVerification
        fields = ['status', 'created_at', 'updated_at']
