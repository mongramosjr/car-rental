from .gcash_service import GcashService
from .paypal_service import PaypalService
from .stripe_service import StripeService
from .cash_service import CashService

def get_payment_service(method):
    services = {
        'gcash': GcashService,
        'paypal': PaypalService,
        'stripe': StripeService,
        'cash': CashService,
    }
    return services.get(method)
