import requests
import json
from django.conf import settings

class PaypalService:
    def __init__(self):
        self.access_token = None
        self.token_type = None
        self.scope = None
        self.app_id = None
        self.expires_in = None
        self.nonce = None
        self._get_access_token()

    def _get_access_token(self):
        # This function fetches an access token for API calls
        auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET)
        headers = {"Accept": "application/json", 
                   "Accept-Language": "en_US", 
                   "Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(
            f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token",
            headers=headers,
            auth=auth,
            data={"grant_type": "client_credentials"}
        )
        response.raise_for_status()
        response_data = response.json()
        self.access_token = response_data['access_token']
        self.token_type = response_data['token_type']
        self.scope = response_data['scope']
        self.app_id = response_data['app_id']
        self.expires_in = response_data['expires_in']
        self.nonce = response_data['nonce']

        return response_data['access_token']

    def checkout_orders(self, payment):
        headers = {
            "Content-Type": "application/json",
            'Accept': 'application/json',
            "Authorization": f"Bearer {self.access_token}",
            "PayPal-Request-Id": payment.paypal_request_id,
        }
        data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": str(payment.amount)
                    },
                    "description": "Car rental payment"
                }
            ]
        }

        response = requests.post(
            f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 201:
            order_data = response.json()
            payment.transaction_id = order_data['id']  # The order ID
            return order_data['id']  # Return the order ID for capture later
        else:
            print(f"Error creating PayPal order: {response.text}")
            return None

    def confirm_order(self, payment):
        order_id = payment.order_id
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }

        data = { 
            "payment_source": { 
                "paypal": { 
                    "name": { "given_name": "John", "surname": "Doe" }, 
                    "email_address": "customer@example.com", 
                    "experience_context": { 
                        "payment_method_preference": "IMMEDIATE_PAYMENT_REQUIRED", 
                        "brand_name": "EXAMPLE INC", 
                        "locale": "en-US", 
                        "landing_page": "LOGIN",
                        "shipping_preference": "SET_PROVIDED_ADDRESS", 
                        "user_action": "PAY_NOW", 
                        "return_url": "https://example.com/returnUrl", 
                        "cancel_url": "https://example.com/cancelUrl" 
                    } 
                }
            } 
        }

        
        response = requests.post(
            f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/confirm-payment-source",
            headers=headers,
            data=json.dumps(data)
        )
        return True

    def process_payment(self, payment):
        order_id = payment.order_id
        headers = {
            "Content-Type": "application/json",
            "PayPal-Request-Id": payment.paypal_request_id,
            "Authorization": f"Bearer {self.access_token}"
        }
        response = requests.post(
            f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
            headers=headers
        )
        
        if response.status_code in (201, 200):  # PayPal might return either status for successful capture
            capture_data = response.json()
            if capture_data['status'] == 'COMPLETED':
                return True, capture_data
            else:
                print(f"Payment not completed: {capture_data['status']}")
                return False, capture_data
        else:
            print(f"Error capturing PayPal payment: {response.text}")
            return False, response.json()
