from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import DriverProfile, User
from employees.models import Employee
from finance.models import BankAccount, LedgerEntry, SchoolAccount
from students.models import Student
from transport.models import Bus, BusAssignment, Route


class MonthlyReportViewTests(APITestCase):
    def setUp(self):
        self.accountant = User.objects.create_user(
            phone_number="0911000010",
            password="pass1234",
            role="ACCOUNTANT",
            full_name="Accountant One",
        )
        self.client.force_authenticate(self.accountant)
        self.account = SchoolAccount.get_current()
        self.bank_account = BankAccount.objects.create(
            bank_name="Bank of Abyssinia",
            account_name="Main Operations",
            account_holder_name="KG Systems",
            account_number="BOA-001",
            initial_balance=Decimal("0.00"),
            current_balance=Decimal("0.00"),
        )

    def test_monthly_report_includes_fee_summary_totals(self):
        LedgerEntry.objects.create(
            account=self.account,
            bank_account=self.bank_account,
            entry_type="REGISTRATION_FEE",
            amount_delta=Decimal("300.00"),
            description="Registration fee",
            created_by=self.accountant,
        )
        LedgerEntry.objects.create(
            account=self.account,
            bank_account=self.bank_account,
            entry_type="TRANSPORT_FEE",
            amount_delta=Decimal("50.00"),
            description="Transport fee",
            created_by=self.accountant,
        )
        LedgerEntry.objects.create(
            account=self.account,
            bank_account=self.bank_account,
            entry_type="MONTHLY_FEE",
            amount_delta=Decimal("100.00"),
            description="Monthly fee",
            created_by=self.accountant,
        )
        LedgerEntry.objects.create(
            account=self.account,
            bank_account=self.bank_account,
            entry_type="MANUAL_INCOME",
            amount_delta=Decimal("25.00"),
            description="Other income",
            created_by=self.accountant,
        )
        LedgerEntry.objects.create(
            account=self.account,
            bank_account=self.bank_account,
            entry_type="EXPENSE_PAYMENT",
            amount_delta=Decimal("-40.00"),
            description="Expense",
            created_by=self.accountant,
        )

        response = self.client.get(reverse("monthly-report"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data["total_income"]), Decimal("475.00"))
        self.assertEqual(Decimal(response.data["total_expense"]), Decimal("40.00"))
        self.assertEqual(Decimal(response.data["profit"]), Decimal("435.00"))
        self.assertEqual(Decimal(response.data["total_registration_fee"]), Decimal("300.00"))
        self.assertEqual(Decimal(response.data["total_transport_fee"]), Decimal("50.00"))
        self.assertEqual(Decimal(response.data["total_monthly_fee"]), Decimal("100.00"))
        self.assertEqual(Decimal(response.data["total_other_income"]), Decimal("25.00"))
        self.assertEqual(len(response.data["entries"]), 5)


class BankAccountApiTests(APITestCase):
    def setUp(self):
        self.director = User.objects.create_user(
            phone_number="0911000011",
            password="pass1234",
            role="DIRECTOR",
            full_name="Director Finance",
        )
        self.client.force_authenticate(self.director)

    def test_director_can_create_bank_account_and_school_total_is_synced(self):
        response = self.client.post(
            reverse("bank-account-list-create"),
            data={
                "bank_name": "Abay Bank",
                "account_name": "Primary Account",
                "account_holder_name": "KG Systems",
                "account_number": "ABAY-001",
                "branch_name": "Addis Branch",
                "swift_code": "ABAYETAA",
                "initial_balance": "1500.00",
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        bank_account = BankAccount.objects.get(account_number="ABAY-001")
        self.assertEqual(bank_account.current_balance, Decimal("1500.00"))
        self.assertEqual(SchoolAccount.get_current().current_balance, Decimal("1500.00"))

    def test_director_can_mark_commercial_bank_as_default(self):
        response = self.client.post(
            reverse("bank-account-list-create"),
            data={
                "bank_name": "Commercial Bank of Ethiopia",
                "account_name": "Main Default",
                "account_holder_name": "KG Systems",
                "account_number": "CBE-001",
                "initial_balance": "2500.00",
                "is_active": True,
                "is_default": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(BankAccount.objects.get(account_number="CBE-001").is_default)


class DriverStudentListTests(APITestCase):
    def setUp(self):
        self.driver = User.objects.create_user(
            phone_number="0911000012",
            password="pass1234",
            role="DRIVER",
            full_name="Driver One",
        )
        self.parent = User.objects.create_user(
            phone_number="0911000013",
            password="pass1234",
            role="PARENT",
            full_name="Parent Driver",
        )
        self.teacher = User.objects.create_user(
            phone_number="0911000014",
            password="pass1234",
            role="TEACHER",
            full_name="Teacher Driver",
        )
        self.other_parent = User.objects.create_user(
            phone_number="0911000015",
            password="pass1234",
            role="PARENT",
            full_name="Other Parent Driver",
        )
        self.driver_profile = DriverProfile.objects.create(user=self.driver, license_number="DRV-101")
        self.teacher_employee = Employee.objects.create(user=self.teacher, role="TEACHER", salary="1000.00")
        self.route = Route.objects.create(name="Driver Route")
        self.bus = Bus.objects.create(
            bus_number="BUS-20",
            plate_number="AA-90909",
            capacity=20,
            driver=self.driver_profile,
            route=self.route,
        )
        self.student = Student.objects.create(
            first_name="Sami",
            last_name="Kid",
            dob="2018-03-03",
            gender="M",
            category="KG",
            grade_level="KG3",
            transport="BUS",
            address="Bole",
            emergency_contact="0913777777",
            parent=self.parent,
            class_teacher=self.teacher_employee,
            class_name="KG3A",
        )
        self.unassigned_student = Student.objects.create(
            first_name="Lidiya",
            last_name="Kid",
            dob="2018-04-04",
            gender="F",
            category="KG",
            grade_level="KG3",
            transport="BUS",
            address="CMC",
            emergency_contact="0913888888",
            parent=self.other_parent,
            class_teacher=self.teacher_employee,
            class_name="KG3A",
        )
        BusAssignment.objects.create(student=self.student, bus=self.bus)
        self.client.force_authenticate(self.driver)

    def test_driver_sees_only_assigned_students_with_family_and_bus_info(self):
        response = self.client.get(reverse("driver-student-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["student_name"], "Sami Kid")
        self.assertEqual(response.data[0]["parent_name"], "Parent Driver")
        self.assertEqual(response.data[0]["address"], "Bole")
        self.assertEqual(response.data[0]["bus_number"], "BUS-20")
        self.assertEqual(response.data[0]["route_name"], "Driver Route")
