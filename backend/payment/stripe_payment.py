from django.db import models
from django.db.models import Q
import json
from .models import BookingPayment

class StripeBookingPayment(BookingPayment):
    client_secret = models.CharField(max_length=100, blank=True, null=True)
    capture_method = models.CharField(max_length=100, blank=True, null=True)
    confirmation_method = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'booking_payments_stripe'

    def save(self, *args, **kwargs):
        self.method = 'stripe'  # Force method to 'stripe'
        super().save(*args, **kwargs)
    
    def set_client_secret(self, client_secret):
        self.client_secret = json.dumps(client_secret) if client_secret else None
    
    def get_client_secret(self):
        return json.loads(self.client_secret) if self.client_secret else None

    def set_capture_method(self, capture_method):
        self.capture_method = json.dumps(capture_method) if capture_method else None

    def get_capture_method(self):
        return json.loads(self.capture_method) if self.capture_method else None

    def set_confirmation_method(self, client_secret):
        self.confirmation_method = json.dumps(confirmation_method) if confirmation_method else None

    def get_confirmation_method(self):
        return json.loads(self.confirmation_method) if self.confirmation_method else None

