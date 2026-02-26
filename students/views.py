from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Student, Parent, Invoice, Payment
from .serializers import StudentSerializer, ParentSerializer, InvoiceSerializer, PaymentSerializer

# ---- Parent Views ----
class ParentListCreateView(generics.ListCreateAPIView):
    queryset = Parent.objects.filter(role='PARENT')
    serializer_class = ParentSerializer
    permission_classes = [IsAuthenticated]


class ParentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Parent.objects.filter(role='PARENT')
    serializer_class = ParentSerializer
    permission_classes = [IsAuthenticated]


# ---- Student Views ----
class StudentListCreateView(generics.ListCreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [AllowAny]


class StudentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]


# ---- Invoice Views ----
class InvoiceListCreateView(generics.ListCreateAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]


# ---- Payment Views ----
class PaymentListCreateView(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(paid_by=self.request.user)
