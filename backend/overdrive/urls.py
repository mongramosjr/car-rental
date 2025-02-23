from django.urls import path
from .views import CreateBookingAPI
from .views import CancelBookingView, ConfirmBookingView, RentedBookingView, StartDrivingView, ReturnCarView

urlpatterns = [
    path('api/bookings/', CreateBookingAPI.as_view(), name='create-booking'),
    path('api/bookings/cancel/<int:booking_id>/', CancelBookingView.as_view(), name='cancel_booking'),
    path('api/bookings/confirm/<int:booking_id>/', ConfirmBookingView.as_view(), name='confirm_booking'),
    path('api/bookings/delivered/<int:booking_id>/', RentedBookingView.as_view(), name='car_delivered'),
    path('api/bookings/start_driving/<int:booking_id>/', StartDrivingView.as_view(), name='start_driving'),
    path('api/bookings/return_car/<int:booking_id>/', ReturnCarView.as_view(), name='return_car'),
]