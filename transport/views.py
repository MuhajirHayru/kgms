from rest_framework import generics, permissions
from .models import Bus, Route, BusAssignment, DriverAlert, FuelRequest
from .serializers import BusSerializer, RouteSerializer, BusAssignmentSerializer, DriverAlertSerializer, FuelRequestSerializer
from chat.services import broadcast_driver_alert, ensure_driver_parent_room


class IsDriver(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "DRIVER")


class IsDirectorOrSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and (
                request.user.role == "DIRECTOR" or request.user.is_superuser
            )
        )

class BusListView(generics.ListCreateAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsDirectorOrSuperuser()]
        return [permissions.IsAuthenticated()]

class RouteListView(generics.ListCreateAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsDirectorOrSuperuser()]
        return [permissions.IsAuthenticated()]

class BusAssignmentListCreateView(generics.ListCreateAPIView):
    serializer_class = BusAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsDirectorOrSuperuser]

    def get_queryset(self):
        queryset = BusAssignment.objects.select_related('student', 'student__parent', 'bus', 'bus__route').all()
        bus_id = self.request.query_params.get("bus_id")
        if bus_id:
            queryset = queryset.filter(bus_id=bus_id)
        return queryset.order_by('bus__bus_number', 'student__first_name', 'student__last_name')

    def perform_create(self, serializer):
        assignment = serializer.save()
        driver_profile = assignment.bus.driver
        if driver_profile and driver_profile.user_id:
            ensure_driver_parent_room(assignment.student, driver_profile.user)


class BusAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BusAssignment.objects.select_related('student', 'student__parent', 'bus', 'bus__route').all()
    serializer_class = BusAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsDirectorOrSuperuser]

class DriverAlertCreateView(generics.CreateAPIView):
    queryset = DriverAlert.objects.all()
    serializer_class = DriverAlertSerializer
    permission_classes = [permissions.IsAuthenticated, IsDriver]

    def perform_create(self, serializer):
        alert = serializer.save(driver=self.request.user.driver_profile)
        broadcast_driver_alert(
            driver_user=self.request.user,
            bus=alert.bus,
            alert_type=alert.alert_type,
            message=alert.message or alert.alert_type,
        )

class FuelRequestCreateView(generics.CreateAPIView):
    queryset = FuelRequest.objects.all()
    serializer_class = FuelRequestSerializer
