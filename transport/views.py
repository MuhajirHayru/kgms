from rest_framework import generics
from .models import Bus, Route, BusAssignment, DriverAlert, FuelRequest
from .serializers import BusSerializer, RouteSerializer, BusAssignmentSerializer, DriverAlertSerializer, FuelRequestSerializer

class BusListView(generics.ListCreateAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer

class RouteListView(generics.ListCreateAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

class BusAssignmentCreateView(generics.CreateAPIView):
    queryset = BusAssignment.objects.all()
    serializer_class = BusAssignmentSerializer

class DriverAlertCreateView(generics.CreateAPIView):
    queryset = DriverAlert.objects.all()
    serializer_class = DriverAlertSerializer

class FuelRequestCreateView(generics.CreateAPIView):
    queryset = FuelRequest.objects.all()
    serializer_class = FuelRequestSerializer