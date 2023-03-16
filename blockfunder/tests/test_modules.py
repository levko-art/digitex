from blockfunder.models import Program, Account
import logging

from exchange.models import Currency

logger = logging.getLogger(__name__)


def test_create_program_check_accounts(db):
    program = Program.objects.create(reward_currency_id=2, is_enable=True, is_visible=True)
    currencies = Currency.objects.filter(id__in=[1, 2, 3, 4, 5])

    for currency in currencies:
        program.deposit_currency.add(currency)
    program.save()

    accounts = Account.objects.filter(program=program, type=Account.Type.DEPOSIT).count()
    assert accounts == 5, 'Unexpected amount of accounts'
