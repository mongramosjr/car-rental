from django.urls import path
from .views import ProcessPaymentView

urlpatterns = [
    path('api/payment/<int:booking_id>/', ProcessPaymentView.as_view(), name='process_payment'),
]
