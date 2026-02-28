from decimal import Decimal

from django.db import transaction

from .models import LedgerEntry, SchoolAccount


def record_account_transaction(*, amount_delta, entry_type, description="", created_by=None):
    delta = Decimal(str(amount_delta))
    with transaction.atomic():
        account = SchoolAccount.get_current()
        account.current_balance = (account.current_balance or Decimal("0")) + delta
        account.save(update_fields=["current_balance", "updated_at"])
        entry = LedgerEntry.objects.create(
            account=account,
            entry_type=entry_type,
            amount_delta=delta,
            description=description,
            created_by=created_by,
        )
    return account, entry
