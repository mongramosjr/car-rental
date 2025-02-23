from django.urls import path
from .views import CarListAPI

urlpatterns = [
    path('api/cars/', CarListAPI.as_view(), name='car-list'),
]
