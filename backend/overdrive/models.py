from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
# from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from fleet_management.models import Vehicle


User = get_user_model()

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Current status of the booking
    STATUS_CHOICES = [
        ('requested', _('Requested')),
        ('canceled', _('Canceled')),
        ('confirmed', _('Confirmed')),
        ('rented', _('Rented')),
        ('driving', _('Driving')),
        ('returned', _('Returned')),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='requested',
    )

    def clean(self):
        # Prevent overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            vehicle=self.vehicle,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
            status__in=["rented", "confirmed", "driving"]  # Only active bookings count
        ).exclude(id=self.id)  # Exclude self in case of updates

        if overlapping_bookings.exists():
            raise ValidationError("This vehicle is already booked during this time.")

    def save(self, *args, **kwargs):
        self.clean()  # Validate before saving
        super().save(*args, **kwargs)

        # Do not update vehicle availability, it must be confirmed manually or automatically if payment is via online
        # self.vehicle.is_available = False  # Assume booked
        # self.vehicle.save()

    def __str__(self):
        return f"Booking for {self.vehicle} from {self.start_time} to {self.end_time}"

    class Meta:
        verbose_name_plural = "Bookings"


class BookingStatusLog(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='status_logs')
    status = models.CharField(
        max_length=10,
        choices=Booking.STATUS_CHOICES
    )
    created_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # User who changed status, regardless of user_type
    def __str__(self):
        return f"{self.booking} - {self.get_status_display()} on {self.created_at}"

    class Meta:
        verbose_name = "Booking Status Log"
        verbose_name_plural = "Booking Status Logs"
        ordering = ['-created_at']  # Most recent first
