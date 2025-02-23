from django.conf import settings

class GcashService:
    def process_payment(self, payment):
        # Here you would implement the GCash API integration
        # This is just a mock for demonstration
        
        # Example parameters you might need:
        # - GCash API key
        # - Payment details
        
        # Assume we have a successful mock transaction
        payment.transaction_id = "GCASH-TRANSACTION-MOCK"
        payment.save()
        return True  # Return True if payment was processed successfully, False otherwise
