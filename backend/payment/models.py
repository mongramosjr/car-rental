from django.db import models
from django.conf import settings
from django.utils import timezone
from overdrive.models import Booking

class BookingPayment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=16, choices=settings.PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=32, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'booking_payments'

    def __str__(self):
        return f"Payment for Booking {self.booking.id} - {self.status}"
