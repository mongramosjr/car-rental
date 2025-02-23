from rest_framework import serializers
from .models import ServiceUser, OTP

class ServiceUserRegistrationSerializer(serializers.ModelSerializer):
    verification_method = serializers.ChoiceField(choices=[('SMS', 'SMS'), ('Email', 'Email')])
    user_type = serializers.ChoiceField(choices=ServiceUser.USER_TYPE_CHOICES)

    class Meta:
        model = ServiceUser
        fields = ['email', 'phone_number', 'password', 'verification_method', 'user_type']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = ServiceUser.objects.create_user(**validated_data)
        return user

class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    email_or_phone = serializers.CharField()

    def validate(self, attrs):
        email_or_phone = attrs['email_or_phone']
        otp = attrs['otp']
        
        if '@' in email_or_phone:
            user = ServiceUser.objects.filter(email=email_or_phone).first()
        else:
            user = ServiceUser.objects.filter(phone_number=email_or_phone).first()

        if not user:
            raise serializers.ValidationError("User not found.")

        otp_object = OTP.objects.filter(user=user, otp=otp).first()
        if not otp_object or not otp_object.is_valid():
            raise serializers.ValidationError("Invalid or expired OTP.")
        
        attrs['user'] = user
        return attrs
