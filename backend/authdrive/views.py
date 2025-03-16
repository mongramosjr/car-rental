# views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ServiceUser, OTP
from .serializers import ServiceUserRegistrationSerializer, OTPVerificationSerializer
import pyotp
from django.core.mail import send_mail
import boto3

def generate_otp():
    totp = pyotp.TOTP(pyotp.random_base32())
    return totp.now()

def send_otp_sms(mobile_number, otp_code, user_id, region_name='us-east-1'):
    sns_client = boto3.client('sns', region_name=region_name)
    message = f"Your one-time password for {user_id} is {otp_code}. Please do not share this with anyone."

    try:
        response = sns_client.publish(
            PhoneNumber=mobile_number,
            Message=message,
            MessageAttributes={
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional'
                }
            }
        )
        return response
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ServiceUserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            otp = generate_otp()
            expiry_time = timezone.now() + timezone.timedelta(minutes=5)  # OTP valid for 5 minutes

            OTP.objects.create(user=user, otp=otp, expires_at=expiry_time)

            if user.verification_method == 'SMS':
                result = send_otp_sms(user.phone_number, otp, user.email or user.phone_number)
                if not result:
                    user.delete()
                    return Response({"detail": "Failed to send OTP via SMS. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif user.verification_method == 'Email':
                subject = 'Your One-Time Password for Registration'
                message = f'Your OTP for {user.email} is: {otp}. Please do not share this with anyone.'
                from_email = 'your-no-reply-email@example.com'  # Replace with your email
                recipient_list = [user.email]
                try:
                    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                except Exception as e:
                    user.delete()
                    return Response({"detail": "Failed to send OTP via email. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"detail": "Invalid verification method."}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": f"OTP sent via {user.verification_method}. Please verify to activate your account."},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPVerificationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.is_active = True
            user.save()

            # Clear all expired OTPs for this user
            OTP.objects.filter(user=user, expires_at__lt=timezone.now()).delete()

            return Response({"message": "Account activated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()  # Blacklist the refresh token

            return Response(
                {"message": "Logout successful. Tokens invalidated."},
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
