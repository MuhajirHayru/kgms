from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from finance.models import BankAccount, LedgerEntry, SchoolAccount
from students.models import GradeCapacitySetting, Invoice, Payment, Student, StudentFeeSetting


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
        GradeCapacitySetting.objects.update_or_create(
            grade_level="KG1",
            defaults={"max_students_per_section": 2},
        )
        self.bank_account = BankAccount.objects.create(
            bank_name="Bank of Abyssinia",
            account_name="Admissions",
            account_holder_name="KG Systems",
            account_number="STU-001",
            initial_balance=Decimal("0.00"),
            current_balance=Decimal("0.00"),
        )

    def test_student_registration_adds_fees_to_balance_and_report(self):
        with patch("students.serializers.random.choice", side_effect=lambda options: options[0]):
            response = self.client.post(
                reverse("student-list-create"),
                data={
                    "first_name": "Sam",
                    "last_name": "Kid",
                    "dob": "2019-01-10",
                    "gender": "M",
                    "category": "KG",
                    "grade_level": "KG1",
                    "transport": "BUS",
                    "address": "Main street",
                    "emergency_contact": "0999999999",
                    "parent_id": self.parent.id,
                    "bank_account_id": self.bank_account.id,
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        student = Student.objects.get(first_name="Sam", last_name="Kid")
        self.assertEqual(student.monthly_tuition_fee, Decimal("100.00"))
        self.assertEqual(student.registration_fee, Decimal("300.00"))
        self.assertEqual(student.transport_fee, Decimal("50.00"))
        self.assertEqual(student.grade_level, "KG1")
        self.assertEqual(student.class_name, "KG1A")

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
        descriptions = list(LedgerEntry.objects.values_list("description", flat=True))
        self.assertTrue(any("KG1 - KG1A" in description for description in descriptions))

    def test_registration_rejects_invalid_grade_for_category(self):
        with patch("students.serializers.random.choice", side_effect=lambda options: options[0]):
            response = self.client.post(
                reverse("student-list-create"),
                data={
                    "first_name": "Sara",
                    "last_name": "Kid",
                    "dob": "2018-01-10",
                    "gender": "F",
                    "category": "KG",
                    "grade_level": "GRADE2",
                    "transport": "FOOT",
                    "parent_id": self.parent.id,
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("grade_level", response.data)

    def test_student_registration_uses_default_bank_when_bank_is_omitted(self):
        self.bank_account.bank_name = "Commercial Bank of Ethiopia"
        self.bank_account.is_default = True
        self.bank_account.save(update_fields=["bank_name", "is_default"])

        with patch("students.serializers.random.choice", side_effect=lambda options: options[0]):
            response = self.client.post(
                reverse("student-list-create"),
                data={
                    "first_name": "Liya",
                    "last_name": "Kid",
                    "dob": "2019-01-10",
                    "gender": "F",
                    "category": "KG",
                    "grade_level": "KG1",
                    "transport": "FOOT",
                    "parent_id": self.parent.id,
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        latest_entry = LedgerEntry.objects.latest("created_at")
        self.assertEqual(latest_entry.bank_account_id, self.bank_account.id)


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


class StudentGradeListingTests(APITestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            phone_number="0911000003",
            password="pass1234",
            role="PARENT",
            full_name="Parent Two",
        )
        GradeCapacitySetting.objects.update_or_create(
            grade_level="KG2",
            defaults={"max_students_per_section": 2},
        )
        GradeCapacitySetting.objects.update_or_create(
            grade_level="GRADE3",
            defaults={"max_students_per_section": 2},
        )
        Student.objects.create(
            first_name="Aman",
            last_name="One",
            dob="2019-01-01",
            gender="M",
            category="KG",
            grade_level="KG2",
            class_name="KG2A",
            transport="FOOT",
            parent=self.parent,
        )
        Student.objects.create(
            first_name="Beth",
            last_name="Two",
            dob="2016-01-01",
            gender="F",
            category="ELEMENTARY",
            grade_level="GRADE3",
            class_name="GRADE3A",
            transport="FOOT",
            parent=self.parent,
        )

    def test_students_can_be_grouped_by_grade(self):
        response = self.client.get(reverse("student-list-by-grade"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["grade_level"], "KG2")
        self.assertEqual(response.data[0]["total_students"], 1)
        self.assertEqual(response.data[0]["sections"][0]["class_name"], "KG2A")
        self.assertEqual(response.data[1]["grade_level"], "GRADE3")
        self.assertEqual(response.data[1]["students"][0]["first_name"], "Beth")


class StudentSectionAssignmentTests(APITestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            phone_number="0911000004",
            password="pass1234",
            role="PARENT",
            full_name="Parent Three",
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
        GradeCapacitySetting.objects.update_or_create(
            grade_level="GRADE1",
            defaults={"max_students_per_section": 2},
        )
        self.bank_account = BankAccount.objects.create(
            bank_name="Abay Bank",
            account_name="Students",
            account_holder_name="KG Systems",
            account_number="STU-002",
            initial_balance=Decimal("0.00"),
            current_balance=Decimal("0.00"),
        )

    def test_students_are_split_into_sections_when_capacity_is_reached(self):
        payload = {
            "dob": "2016-01-10",
            "gender": "M",
            "category": "ELEMENTARY",
            "grade_level": "GRADE1",
            "transport": "FOOT",
            "parent_id": self.parent.id,
            "bank_account_id": self.bank_account.id,
        }

        with patch("students.serializers.random.choice", side_effect=lambda options: options[-1]):
            for first_name in ["Ali", "Ben", "Cal"]:
                response = self.client.post(
                    reverse("student-list-create"),
                    data={**payload, "first_name": first_name, "last_name": "Kid"},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        classes = list(
            Student.objects.filter(grade_level="GRADE1")
            .order_by("first_name")
            .values_list("class_name", flat=True)
        )
        self.assertEqual(classes, ["GRADE1A", "GRADE1A", "GRADE1B"])

    def test_students_can_be_randomly_placed_into_any_available_section(self):
        Student.objects.create(
            first_name="Existing",
            last_name="A",
            dob="2016-01-01",
            gender="M",
            category="ELEMENTARY",
            grade_level="GRADE1",
            class_name="GRADE1A",
            transport="FOOT",
            parent=self.parent,
        )
        Student.objects.create(
            first_name="Existing",
            last_name="B",
            dob="2016-01-01",
            gender="M",
            category="ELEMENTARY",
            grade_level="GRADE1",
            class_name="GRADE1B",
            transport="FOOT",
            parent=self.parent,
        )

        payload = {
            "first_name": "Dana",
            "last_name": "Kid",
            "dob": "2016-01-10",
            "gender": "F",
            "category": "ELEMENTARY",
            "grade_level": "GRADE1",
            "transport": "FOOT",
            "parent_id": self.parent.id,
            "bank_account_id": self.bank_account.id,
        }

        with patch("students.serializers.random.choice", side_effect=lambda options: options[-1]):
            response = self.client.post(reverse("student-list-create"), data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Student.objects.get(first_name="Dana").class_name, "GRADE1B")


class GradeCapacitySettingViewTests(APITestCase):
    def setUp(self):
        self.director = User.objects.create_user(
            phone_number="0911000005",
            password="pass1234",
            role="DIRECTOR",
            full_name="Director Two",
        )
        self.client.force_authenticate(self.director)

    def test_capacity_list_returns_grade_settings(self):
        response = self.client.get(reverse("grade-capacity-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item["grade_level"] == "KG1" for item in response.data))


class MonthlyPaymentReportDescriptionTests(APITestCase):
    def setUp(self):
        self.accountant = User.objects.create_user(
            phone_number="0911000006",
            password="pass1234",
            role="ACCOUNTANT",
            full_name="Accountant Three",
        )
        self.parent = User.objects.create_user(
            phone_number="0911000007",
            password="pass1234",
            role="PARENT",
            full_name="Parent Four",
        )
        self.student = Student.objects.create(
            first_name="Mahi",
            last_name="Kid",
            dob="2016-01-01",
            gender="F",
            category="ELEMENTARY",
            grade_level="GRADE2",
            class_name="GRADE2B",
            transport="FOOT",
            parent=self.parent,
            monthly_tuition_fee=Decimal("200.00"),
        )
        self.invoice = Invoice.objects.create(
            student=self.student,
            month="2026-03",
            amount=Decimal("200.00"),
            due_date="2026-03-05",
            is_paid=False,
        )
        self.bank_account = BankAccount.objects.create(
            bank_name="Dashen Bank",
            account_name="Fees",
            account_holder_name="KG Systems",
            account_number="PAY-001",
            initial_balance=Decimal("0.00"),
            current_balance=Decimal("0.00"),
        )
        self.client.force_authenticate(self.accountant)

    def test_manual_monthly_payment_report_includes_grade_and_section(self):
        response = self.client.post(
            reverse("payment-create"),
            data={
                "invoice_id": self.invoice.id,
                "amount": "200.00",
                "bank_account_id": self.bank_account.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        entry = LedgerEntry.objects.filter(entry_type="MONTHLY_FEE").latest("created_at")
        self.assertIn("GRADE2 - GRADE2B", entry.description)
        self.assertIn("2026-03", entry.description)
