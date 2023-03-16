import decimal
from datetime import timedelta

from marketdata_history.models import CurrencyPairLog
from django.utils import timezone
from blockfunder.models import *
import pytest


@pytest.fixture(scope='function')
def program(db):
    program_fixture = Program()
    program_fixture.deposit_currency_id = 1
    program_fixture.reward_currency_id = 2
    program_fixture.is_enable = True
    program_fixture.is_visible = True
    program_fixture.rate = decimal.Decimal(10.0)
    program_fixture.hard_cap = decimal.Decimal(100.0)
    program_fixture.begin_date = timezone.now() - timedelta(days=5)
    program_fixture.end_date = program_fixture.begin_date + timedelta(days=30)
    program_fixture.save()

    return program_fixture


@pytest.fixture(scope='function')
def currency_pair_log(db):
    currency_pair_log_fixture = CurrencyPairLog()
    currency_pair_log_fixture.date = timezone.now()
    currency_pair_log_fixture.currency_pair_id = 5
    currency_pair_log_fixture.mark_price = 10
    currency_pair_log_fixture.save()

    return currency_pair_log_fixture
