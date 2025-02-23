from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import BookingPayment
from .serializers import BookingPaymentSerializer
from .services import get_payment_service

class ProcessPaymentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        payment_data = request.data
        payment_data['booking'] = booking_id  # Set the booking ID

        payment_serializer = BookingPaymentSerializer(data=payment_data)
        if payment_serializer.is_valid():
            payment = payment_serializer.save()

            # Get the appropriate payment service based on method
            service = get_payment_service(payment.method)
            if service:
                # Here, make sure to instantiate the service if it's not already an instance
                service_instance = service()
                success = service_instance.process_payment(payment)
                if success:
                    payment.status = 'completed'
                    payment.save()
                    return Response({"status": "Payment processed successfully"}, status=status.HTTP_200_OK)
                else:
                    payment.status = 'failed'
                    payment.save()
                    return Response({"status": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"status": "Invalid payment method"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(payment_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
