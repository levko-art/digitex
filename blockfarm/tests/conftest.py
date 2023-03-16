import decimal
import string
from datetime import timedelta
from random import choice, randint

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from blockfarm.models import *


# FixMe: add correct attributes for create class instances

def random_slug():
    allchar = string.ascii_letters + string.digits
    un = "".join(choice(allchar) for x in range(randint(5, 10)))
    return  un

@pytest.fixture(scope='function')
def program(db):
    program_fixture = Program()
    program_fixture.slug = random_slug()
    program_fixture.is_enable = True
    program_fixture.is_visible = True
    program_fixture.begin_date = timezone.now() - timedelta(days=5)
    program_fixture.emit_duration = timedelta(days=30)
    program_fixture.reward_currency_id = 2
    program_fixture.transaction_currency_id = 1
    program_fixture.iteration = timedelta(hours=1)
    program_fixture.save()

    acr = program_fixture.reward_account
    acr.treasury_id = 2
    acr.save()
    acd = program_fixture.deposit_account
    acd.treasury_id = 1
    acd.save()

    return program_fixture


@pytest.fixture(scope='function')
def program_with_reward(db):
    program_fixture = Program()
    program_fixture.slug = random_slug()
    program_fixture.is_enable = True
    program_fixture.is_visible = True
    program_fixture.begin_date = timezone.now() - timedelta(days=5)
    program_fixture.emit_duration = timedelta(days=30)
    program_fixture.reward_currency_id = 2
    program_fixture.transaction_currency_id = 1
    program_fixture.iteration = timedelta(hours=1)
    program_fixture.save()

    acr = program_fixture.reward_account
    acr.balance = decimal.Decimal('720') # 1 by hour / iteration
    acr.treasury_id = 2
    acr.save()
    acd = program_fixture.deposit_account
    acd.treasury_id = 1
    acd.save()
    return program_fixture


@pytest.fixture(scope='function')
def short_program_with_reward(db):
    program_fixture = Program()
    program_fixture.slug = random_slug()
    program_fixture.is_enable = True
    program_fixture.is_visible = True
    program_fixture.begin_date = timezone.now() - timedelta(days=5)
    program_fixture.emit_duration = timedelta(hours=1)
    program_fixture.reward_currency_id = 2
    program_fixture.transaction_currency_id = 1
    program_fixture.iteration = timedelta(hours=1)
    program_fixture.save()

    acr = program_fixture.reward_account
    acr.balance = decimal.Decimal('720') # 1 by hour / iteration
    acr.treasury_id = 2
    acr.save()
    acd = program_fixture.deposit_account
    acd.treasury_id = 1
    acd.save()
    return program_fixture

@pytest.fixture(scope='function')
def short_program_with_reward_30min(db):
    program_fixture = Program()
    program_fixture.slug = random_slug()
    program_fixture.is_enable = True
    program_fixture.is_visible = True
    program_fixture.begin_date = timezone.now() - timedelta(days=5)
    program_fixture.emit_duration = timedelta(hours=1)
    program_fixture.reward_currency_id = 2
    program_fixture.transaction_currency_id = 1
    program_fixture.iteration = timedelta(minutes=30)
    program_fixture.save()

    acr = program_fixture.reward_account
    acr.balance = decimal.Decimal('720') # 1 by hour / iteration
    acr.treasury_id = 2
    acr.save()
    acd = program_fixture.deposit_account
    acd.treasury_id = 1
    acd.save()
    return program_fixture


@pytest.fixture(scope='function')
def deposit_wallet(db, program, verified_user):
    wallet_fixture = Wallet()
    wallet_fixture.type = Wallet.Type.DEPOSIT
    wallet_fixture.balance = 10
    wallet_fixture.program = program
    wallet_fixture.user = User.objects.get(email=verified_user)
    wallet_fixture.save()
    return wallet_fixture


@pytest.fixture(scope='function')
def reward_wallet(db, program, verified_user):
    wallet_fixture = Wallet()
    wallet_fixture.type = Wallet.Type.REWARD
    wallet_fixture.balance = 0
    wallet_fixture.program = program
    wallet_fixture.user = User.objects.get(email=verified_user)
    wallet_fixture.save()
    return wallet_fixture


@pytest.fixture(scope='function')
def deposit_account(db, program):
    account_fixture = program.deposit_account
    account_fixture.treasury_id = 1
    account_fixture.balance = 10
    account_fixture.save()
    return account_fixture


@pytest.fixture(scope='function')
def reward_account(db, program):
    account_fixture = program.reward_account
    account_fixture.treasury_id = 2
    account_fixture.save()
    return account_fixture
