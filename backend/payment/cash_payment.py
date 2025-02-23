from django.db import models
import json
from .models import BookingPayment

class CashBookingPayment(BookingPayment):
   
    class Meta:
        db_table = 'booking_payments_cash'
