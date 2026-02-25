from rest_framework import serializers
from .models import Bus, Route, BusAssignment, DriverAlert, FuelRequest

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = '__all__'

class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = '__all__'

class BusAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusAssignment
        fields = '__all__'

class DriverAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverAlert
        fields = '__all__'

class FuelRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelRequest
        fields = '__all__'