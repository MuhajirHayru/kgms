from django.urls import path
from .views import BusListView, RouteListView, BusAssignmentCreateView, DriverAlertCreateView, FuelRequestCreateView

urlpatterns = [
    path('buses/', BusListView.as_view(), name='bus-list'),
    path('routes/', RouteListView.as_view(), name='route-list'),
    path('assignments/', BusAssignmentCreateView.as_view(), name='bus-assignment-create'),
    path('alerts/', DriverAlertCreateView.as_view(), name='driver-alert-create'),
    path('fuel-requests/', FuelRequestCreateView.as_view(), name='fuel-request-create'),
]