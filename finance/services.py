from decimal import Decimal

from django.db import transaction

from .models import BankAccount, LedgerEntry, SchoolAccount


def record_account_transaction(*, bank_account=None, amount_delta, entry_type, description="", created_by=None):
    delta = Decimal(str(amount_delta))
    with transaction.atomic():
        if bank_account is None:
            bank_account = BankAccount.get_default()
        if isinstance(bank_account, int):
            bank_account = BankAccount.objects.get(pk=bank_account, is_active=True)
        if bank_account is None:
            raise BankAccount.DoesNotExist("No active bank account is configured for this transaction.")

        account = SchoolAccount.get_current()
        bank_account.current_balance = (bank_account.current_balance or Decimal("0")) + delta
        bank_account.save(update_fields=["current_balance", "updated_at"])
        account.refresh_from_db()
        entry = LedgerEntry.objects.create(
            account=account,
            bank_account=bank_account,
            entry_type=entry_type,
            amount_delta=delta,
            description=description,
            created_by=created_by,
        )
    return account, entry
