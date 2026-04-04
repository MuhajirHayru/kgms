from rest_framework import serializers
from .models import Bus, Route, BusAssignment, DriverAlert, FuelRequest

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = '__all__'

class BusSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.user.full_name', read_only=True)
    route_name = serializers.CharField(source='route.name', read_only=True)

    class Meta:
        model = Bus
        fields = '__all__'

class BusAssignmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    parent_name = serializers.CharField(source='student.parent.full_name', read_only=True)
    parent_phone = serializers.CharField(source='student.parent.phone_number', read_only=True)
    bus_number = serializers.CharField(source='bus.bus_number', read_only=True)
    bus_plate_number = serializers.CharField(source='bus.plate_number', read_only=True)
    route_name = serializers.CharField(source='bus.route.name', read_only=True)

    class Meta:
        model = BusAssignment
        fields = [
            'id',
            'student',
            'student_name',
            'parent_name',
            'parent_phone',
            'bus',
            'bus_number',
            'bus_plate_number',
            'route_name',
            'assigned_date',
        ]
        read_only_fields = ['id', 'assigned_date', 'student_name', 'parent_name', 'parent_phone', 'bus_number', 'bus_plate_number', 'route_name']

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip()

    def validate(self, attrs):
        student = attrs.get('student') or getattr(self.instance, 'student', None)
        bus = attrs.get('bus') or getattr(self.instance, 'bus', None)
        if student and bus and student.transport != 'BUS':
            raise serializers.ValidationError({'student': 'Only BUS transport students can be assigned to a bus.'})

        if student:
            qs = BusAssignment.objects.filter(student=student)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({'student': 'This student already has a bus assignment. Update the existing assignment instead.'})
        return attrs

class DriverAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverAlert
        fields = '__all__'
        read_only_fields = ['driver']

class FuelRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelRequest
        fields = '__all__'
