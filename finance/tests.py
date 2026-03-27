from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from finance.models import LedgerEntry, SchoolAccount


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

    def test_monthly_report_includes_fee_summary_totals(self):
        LedgerEntry.objects.create(
            account=self.account,
            entry_type="REGISTRATION_FEE",
            amount_delta=Decimal("300.00"),
            description="Registration fee",
            created_by=self.accountant,
        )
        LedgerEntry.objects.create(
            account=self.account,
            entry_type="TRANSPORT_FEE",
            amount_delta=Decimal("50.00"),
            description="Transport fee",
            created_by=self.accountant,
        )
        LedgerEntry.objects.create(
            account=self.account,
            entry_type="MONTHLY_FEE",
            amount_delta=Decimal("100.00"),
            description="Monthly fee",
            created_by=self.accountant,
        )
        LedgerEntry.objects.create(
            account=self.account,
            entry_type="MANUAL_INCOME",
            amount_delta=Decimal("25.00"),
            description="Other income",
            created_by=self.accountant,
        )
        LedgerEntry.objects.create(
            account=self.account,
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
