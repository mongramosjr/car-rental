from .models import Booking, BookingStatusLog

def update_booking_status(booking, new_status, user=None):
    if booking.status != new_status:
        booking.status = new_status
        booking.save()
        BookingStatusLog.objects.create(
            booking=booking,
            status=new_status,
            user=user
        )
        # Update vehicle availability based on status
        if new_status in ['canceled', 'returned']:
            booking.vehicle.is_available = True
        elif new_status == 'confirmed':
            booking.vehicle.is_available = False

        booking.vehicle.save()
