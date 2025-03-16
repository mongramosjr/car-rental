from django.urls import path
from .views import CarListAPI, CarCreateAPI, CarDetailAPI, CarUpdateAPI

urlpatterns = [
    path('api/cars/', CarListAPI.as_view(), name='car-list'),
    path('api/cars/create/', CarCreateAPI.as_view(), name='car-create'),
    path('api/cars/<int:pk>/update/', CarUpdateAPI.as_view(), name='car-update'),
    path('api/cars/<int:pk>/', CarDetailAPI.as_view(), name='car-detail'),
]
