from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Car
from .serializers import CarSerializer

class CarListAPI(generics.ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    queryset = Car.objects.filter(is_available=True)
    serializer_class = CarSerializer
