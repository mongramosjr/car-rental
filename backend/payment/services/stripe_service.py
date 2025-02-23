import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    def process_payment(self, payment):
        try:
            # Create a PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=int(payment.amount * 100),  # Convert to cents for Stripe
                currency="usd",
                description="Car rental payment",
                automatic_payment_methods={"enabled": True},
            )

            # If you need to charge a card right away, you would confirm the intent here
            # For simplicity, we're just creating the intent
            payment.transaction_id = intent['id']  # The intent ID
            payment.status = intent["status"] # requires_payment_method, requires_confirmation,
            payment.client_secret = intent["client_secret"]
            payment.capture_method = intent["capture_method"]
            payment.confirmation_method = intent["confirmation_method"]
            payment.save()
            return True
        except stripe.error.StripeError as e:
            # Handle Stripe errors
            return False

    def confirm_payment_intent(self, payment):
        try:
            intent = stripe.PaymentIntent.confirm(
                payment.transaction_id,
                payment_method="pm_card_visa")
            return True
        except stripe.error.StripeError as e:
            # Handle Stripe errors
            return False

    def capture_payment_intent(self, payment):
        try:
            intent = stripe.PaymentIntent.capture(
                payment.transaction_id,
                payment_method="pm_card_visa")
            return True
        except stripe.error.StripeError as e:
            # Handle Stripe errors
            return False

