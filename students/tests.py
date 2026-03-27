from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from finance.models import LedgerEntry, SchoolAccount
from students.models import Invoice, Payment, Student, StudentFeeSetting


class StudentRegistrationFlowTests(APITestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            phone_number="0911000001",
            password="pass1234",
            role="PARENT",
            full_name="Parent One",
        )
        StudentFeeSetting.objects.update_or_create(
            id=1,
            defaults={
                "kg_monthly_fee": Decimal("100.00"),
                "elementary_monthly_fee": Decimal("200.00"),
                "registration_fee": Decimal("300.00"),
                "bus_transport_fee": Decimal("50.00"),
            },
        )

    def test_student_registration_adds_fees_to_balance_and_report(self):
        response = self.client.post(
            reverse("student-list-create"),
            data={
                "first_name": "Sam",
                "last_name": "Kid",
                "dob": "2019-01-10",
                "gender": "M",
                "category": "KG",
                "transport": "BUS",
                "address": "Main street",
                "emergency_contact": "0999999999",
                "parent_id": self.parent.id,
                "class_name": "KG-1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        student = Student.objects.get(first_name="Sam", last_name="Kid")
        self.assertEqual(student.monthly_tuition_fee, Decimal("100.00"))
        self.assertEqual(student.registration_fee, Decimal("300.00"))
        self.assertEqual(student.transport_fee, Decimal("50.00"))

        invoice = Invoice.objects.get(student=student)
        self.assertTrue(invoice.is_paid)
        self.assertEqual(invoice.amount, Decimal("100.00"))
        self.assertTrue(Payment.objects.filter(invoice=invoice, amount=Decimal("100.00")).exists())

        account = SchoolAccount.get_current()
        self.assertEqual(account.current_balance, Decimal("450.00"))

        entry_types = list(LedgerEntry.objects.values_list("entry_type", flat=True))
        self.assertCountEqual(
            entry_types,
            ["REGISTRATION_FEE", "TRANSPORT_FEE", "MONTHLY_FEE"],
        )


class StudentFeeSettingViewTests(APITestCase):
    def setUp(self):
        self.director = User.objects.create_user(
            phone_number="0911000002",
            password="pass1234",
            role="DIRECTOR",
            full_name="Director One",
        )
        self.client.force_authenticate(self.director)

    def test_director_can_update_student_fee_settings(self):
        response = self.client.put(
            reverse("student-fee-setting"),
            data={
                "kg_monthly_fee": "125.00",
                "elementary_monthly_fee": "225.00",
                "registration_fee": "350.00",
                "bus_transport_fee": "60.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        setting = StudentFeeSetting.get_current()
        self.assertEqual(setting.kg_monthly_fee, Decimal("125.00"))
        self.assertEqual(setting.elementary_monthly_fee, Decimal("225.00"))
        self.assertEqual(setting.registration_fee, Decimal("350.00"))
        self.assertEqual(setting.bus_transport_fee, Decimal("60.00"))
