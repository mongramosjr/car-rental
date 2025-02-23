from django.apps import AppConfig


class PaymentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payment'

    def ready(self):
        # Import additional models to ensure they're registered
        from . import paypal_payment
        from . import stripe_payment
        from . import cash_payment
        from . import gcash_payment