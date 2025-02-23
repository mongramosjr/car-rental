class CashService:
    def process_payment(self, payment):
        # For cash payments, you might just confirm the status
        # No actual processing here, but you might want to:
        # - Update booking status to "paid"
        # - Generate a receipt or invoice
        # - Log the transaction
        
        payment.transaction_id = "CASH-PAYMENT-MOCK"  # Or leave this empty if not applicable
        payment.save()
        return True  # Assuming cash payment is handled outside of digital processing
