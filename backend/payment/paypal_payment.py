from django.db import models
from django.db.models import Q
import json
from .models import BookingPayment

class PayPalBookingPayment(BookingPayment):
    paypal_request_id = models.CharField(max_length=38, blank=True, null=True)
    order_id = models.CharField(max_length=100, blank=True, null=True)
    payer = models.JSONField(blank=True, null=True)
    payment_source = models.JSONField(blank=True, null=True)
    links = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'booking_payments_paypal'

    def save(self, *args, **kwargs):
        self.method = 'paypal'  # Force method to 'paypal'
        super().save(*args, **kwargs)
    
    def set_payer(self, payer_data):
        self.payer = json.dumps(payer_data) if payer_data else None
    
    def get_payer(self):
        return json.loads(self.payer) if self.payer else None
    
    def set_payment_source(self, source_data):
        self.payment_source = json.dumps(source_data) if source_data else None
    
    def get_payment_source(self):
        return json.loads(self.payment_source) if self.payment_source else None
    
    def set_links(self, links_data):
        self.links = json.dumps(links_data) if links_data else None
    
    def get_links(self):
        return json.loads(self.links) if self.links else None