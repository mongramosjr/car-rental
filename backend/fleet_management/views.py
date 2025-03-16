from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Car, Owner
from .serializers import CarSerializer
from django.shortcuts import get_object_or_404


# Public endpoint to list all available cars
class CarListAPI(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required

    def get(self, request):
        cars = Car.objects.filter(is_available=True)
        serializer = CarSerializer(cars, many=True, context={'request': request}) # Pass request in context
        return Response(serializer.data)

# Authenticated endpoint to create a new car
class CarCreateAPI(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):

        try:
            owner = Owner.objects.get(user=request.user)
        except Owner.DoesNotExist:
            return Response(
                {"detail": "User is not registered as an owner"},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        data['owner'] = owner.id

        serializer = CarSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Public endpoint to get car details
class CarDetailAPI(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required

    def get(self, request, pk):
        car = get_object_or_404(Car, pk=pk, is_available=True)
        serializer = CarSerializer(car, context={'request': request})
        return Response(serializer.data)

# Authenticated endpoint to update a car
class CarUpdateAPI(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def put(self, request, pk):
        car = get_object_or_404(Car, pk=pk)

        if car.owner.user != request.user:
            return Response(
                {"detail": "You can only update your own cars"},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        serializer = CarSerializer(car, data=data, partial=True, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
