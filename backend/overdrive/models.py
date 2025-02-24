from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
# from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime
from django.utils.translation import gettext_lazy as _
from fleet_management.models import Car


User = get_user_model()

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
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
    def __str__(self):
        return f"Booking for {self.car} from {self.start_time} to {self.end_time}"

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
