from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,)


from django.conf import settings
from django.conf.urls.static import static
from accounts.views import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
urlpatterns = [
    path('admin/', admin.site.urls),

    # Accounts
    path('api/accounts/', include('accounts.urls')),

    # Employees
    path('api/employees/', include('employees.urls')),

    # Transport
    path('api/transport/', include('transport.urls')),

    # Finance
    path('api/finance/', include('finance.urls')),
    # Students
    path('api/students/', include('students.urls')),
     path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



