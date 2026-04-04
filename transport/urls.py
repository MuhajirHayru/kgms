from django.urls import path
from .views import (
    BusAssignmentDetailView,
    BusAssignmentListCreateView,
    BusListView,
    DriverAlertCreateView,
    FuelRequestCreateView,
    RouteListView,
)

urlpatterns = [
    path('buses/', BusListView.as_view(), name='bus-list'),
    path('routes/', RouteListView.as_view(), name='route-list'),
    path('assignments/', BusAssignmentListCreateView.as_view(), name='bus-assignment-list-create'),
    path('assignments/create/', BusAssignmentListCreateView.as_view(), name='bus-assignment-create'),
    path('assignments/<int:pk>/', BusAssignmentDetailView.as_view(), name='bus-assignment-detail'),
    path('alerts/', DriverAlertCreateView.as_view(), name='driver-alert-create'),
    path('fuel-requests/', FuelRequestCreateView.as_view(), name='fuel-request-create'),
]
