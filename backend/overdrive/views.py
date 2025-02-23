from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth import get_user_model

from fleet_management.models import Car
from .serializers import BookingSerializer
from fleet_management.serializers import CarSerializer
from .models import Booking
from .utils import update_booking_status

User = get_user_model()


class CreateBookingAPI(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def get_user_profile(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    def perform_create(self, serializer):
        car = Car.objects.get(id=self.request.data.get('car'))
        start_time = self.request.data.get('start_time')
        end_time = self.request.data.get('end_time')

        # Convert string dates to datetime objects if they are strings
        if isinstance(start_time, str):
            start_time = timezone.datetime.fromisoformat(start_time)
        if isinstance(end_time, str):
            end_time = timezone.datetime.fromisoformat(end_time)

        # Check user profile
        profile = self.get_user_profile(self.request.user)

        if not profile:
            raise PermissionDenied("User profile not found. Cannot create booking.")
        # Check if the user has permissions to book (e.g., only customers can book)
        if profile.user_type != 'customer':
            raise PermissionDenied("Only customers can create bookings.")

        # TODO: is this required?
        user = User.objects.get(id=self.request.data.get('user'))
        if user.email != self.request.user.email:
            raise PermissionDenied("Only customers can create bookings. Invalid user.")

        # Calculate total price based on duration
        duration = (end_time - start_time).total_seconds() / 3600  # hours
        total_price = Decimal(duration) * car.price_per_hour

        # Save the booking with initial status 'requested'
        booking = serializer.save(user=self.request.user, car=car, start_time=start_time, end_time=end_time, total_price=total_price)

        # Update the booking status to 'requested'
        update_booking_status(booking, 'requested', user=self.request.user)


class BaseBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def get_user_profile(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    def check_permissions(self, request):
        super().check_permissions(request)


class CancelBookingView(BaseBookingView):
    authentication_classes = [JWTAuthentication]
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            profile = self.get_user_profile(request.user)

            if not profile:
                return Response({"error": "User profile not found."}, status=status.HTTP_403_FORBIDDEN)

            if profile.is_car_owner() or booking.user == request.user:
                update_booking_status(booking, 'canceled', user=request.user)
                return Response({"message": "Booking canceled successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "You do not have permission to cancel this booking."}, status=status.HTTP_403_FORBIDDEN)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)


class ConfirmBookingView(BaseBookingView):
    authentication_classes = [JWTAuthentication]
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            profile = self.get_user_profile(request.user)

            if not profile or not profile.is_car_owner():
                return Response({"error": "Only car owners can confirm bookings."}, status=status.HTTP_403_FORBIDDEN)

            update_booking_status(booking, 'confirmed', user=request.user)
            return Response({"message": "Booking confirmed."}, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)


class RentedBookingView(BaseBookingView):
    authentication_classes = [JWTAuthentication]
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            profile = self.get_user_profile(request.user)

            if not profile or not profile.is_car_owner():
                return Response({"error": "Only car owners can confirm delivery of car to the customer."}, status=status.HTTP_403_FORBIDDEN)

            update_booking_status(booking, 'rented', user=request.user)
            return Response({"message": "Car delivered to the customer."}, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)


class StartDrivingView(BaseBookingView):
    authentication_classes = [JWTAuthentication]
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)

            if booking.user != request.user:
                return Response({"error": "Only the booking user can start driving."}, status=status.HTTP_403_FORBIDDEN)

            update_booking_status(booking, 'driving', user=request.user)
            return Response({"message": "Driving started."}, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)


class ReturnCarView(BaseBookingView):
    authentication_classes = [JWTAuthentication]
    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(id=booking_id)
            profile = self.get_user_profile(request.user)

            if not profile or not profile.is_car_owner():
                return Response({"error": "Only car owners can return cars."}, status=status.HTTP_403_FORBIDDEN)

            update_booking_status(booking, 'returned', user=request.user)
            return Response({"message": "Car returned."}, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)
