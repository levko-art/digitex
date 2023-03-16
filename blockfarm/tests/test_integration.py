import decimal
from django.contrib.auth.models import User
from django.db.models import Sum
import string
from blockfarm import tasks
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from blockfarm.models import Transaction, ClaimReward, Account, Reward, Wallet, Program
from exchange.models import MainTrader
from random import choice, randint


# Approve
def test_create_reward_normal(client, verified_user, program, deposit_wallet, deposit_account, httpserver):
    settings.TREASURY_URL = httpserver.url_for("")[:-1]
    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets/100/transfer/to-main", query_string=f"wallet2={deposit_account.treasury_id}&amount=10").respond_with_json([])
    total_stack_amount_before_stack = deposit_wallet.balance
    total_account_stack_amount_before_stack = deposit_account.balance
    Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.STAKE, program=program)
    tasks.calculating_rewards()
    total_stack_amount_after_stack = Wallet.objects.get(program=program, user=deposit_wallet.user, type=Wallet.Type.DEPOSIT).balance
    total_account_stack_amount_after_stack = Account.objects.get(pk=deposit_account.id).balance
    assert total_stack_amount_after_stack == total_stack_amount_before_stack + 10, 'Total user wallet stack amount has been changed'
    assert total_account_stack_amount_after_stack == total_account_stack_amount_before_stack + 10, 'Total program account stack amount has been changed'


# Approve
def test_create_reward_empty_stack_zero(client, verified_user, program, deposit_wallet, deposit_account, httpserver):
    settings.TREASURY_URL = httpserver.url_for("")[:-1]
    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets/100/transfer/to-main", query_string=f"wallet2={deposit_account.treasury_id}&amount=0").respond_with_json([])
    total_stack_amount_before_stack = deposit_wallet.balance
    total_account_stack_amount_before_stack = deposit_account.balance
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=0, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.STAKE, program=program)
    assert tx.status == Transaction.Status.SUCCESS
    tasks.calculating_rewards()
    total_stack_amount_after_stack = Wallet.objects.get(program=program, user=deposit_wallet.user, type=Wallet.Type.DEPOSIT).balance
    total_account_stack_amount_after_stack = Account.objects.get(pk=deposit_account.id).balance
    assert total_stack_amount_before_stack == total_stack_amount_after_stack, 'Total stack amount has been changed'
    assert total_account_stack_amount_after_stack == total_account_stack_amount_before_stack, 'Total program account stack amount has been changed'


# Approve
def test_create_reward_2_iterations(client, verified_user, httpserver):
    program = Program.objects.create(slug="".join(choice(string.ascii_letters + string.digits) for x in range(randint(5, 10))), transaction_currency_id=1, reward_currency_id=2, is_enable=True, is_visible=True, begin_date=timezone.now()-timedelta(days=5), emit_duration=timedelta(hours=1), iteration=timedelta(minutes=30))

    deposit_account = Account.objects.get(type=Account.Type.DEPOSIT, program=program)
    deposit_account.balance = 100
    deposit_account.treasury_id = 1
    deposit_account.save()
    reward_account = Account.objects.get(type=Account.Type.REWARD, program=program)
    reward_account.balance = 1
    reward_account.treasury_id = 2
    reward_account.save()
    deposit_wallet = Wallet.objects.create(type=Wallet.Type.DEPOSIT, balance=100, program=program, user=User.objects.get(email=verified_user))
    reward_wallet = Wallet.objects.create(type=Wallet.Type.REWARD, balance=100, program=program, user=User.objects.get(email=verified_user))

    program.reward_currency.custodian_scale = 8
    program.reward_currency.save()

    settings.TREASURY_URL = httpserver.url_for("")[:-1]
    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets/100/transfer/to-main", query_string=f"wallet2={deposit_account.treasury_id}&amount=10000").respond_with_json([])
    httpserver.expect_request("/wallets/100/transfer/to-main", query_string=f"wallet2={deposit_account.treasury_id}&amount=15").respond_with_json([])

    tx_1 = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10000, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.STAKE, program=program)
    assert tx_1.status == Transaction.Status.SUCCESS
    Transaction.objects.filter(id=tx_1.id).update(created_at=program.begin_date - timedelta(minutes=30))
    tasks.calculating_rewards()

    real_reward = Reward.objects.get(program=program, user__email=verified_user)
    real_reward_amount = real_reward.amount
    to_1_reward = 0.5

    assert real_reward_amount == to_1_reward, 'Reward account balance is not equal to reward computing amount'
    assert Wallet.objects.get(user__email=verified_user, type=Wallet.Type.REWARD, program=program).balance == 100.5

    tx_2 = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=15, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.STAKE, program=program)
    assert tx_2.status == Transaction.Status.SUCCESS
    Transaction.objects.filter(id=tx_2.id).update(created_at=program.begin_date + timedelta(minutes=30))
    tasks.calculating_rewards()

    real_reward = Reward.objects.filter(program=program, user__email=verified_user)[0]
    real_reward_amount = real_reward.amount
    to_2_reward = 0.5
    assert real_reward_amount == to_2_reward, 'Reward account balance is not equal to reward computing amount'
    assert Wallet.objects.get(user__email=verified_user, type=Wallet.Type.REWARD).balance == 101


# Approve
def test_create_reward_transaction_at_the_same_time_with_iteration(client, verified_user, httpserver):
    program = Program.objects.create(slug="".join(choice(string.ascii_letters + string.digits) for x in range(randint(5, 10))), transaction_currency_id=1, reward_currency_id=2, is_enable=True, is_visible=True, begin_date=timezone.now()-timedelta(days=5), emit_duration=timedelta(hours=1), iteration=timedelta(minutes=30))

    deposit_account = Account.objects.get(type=Account.Type.DEPOSIT, program=program)
    deposit_account.balance = 100
    deposit_account.treasury_id = 1
    deposit_account.save()
    reward_account = Account.objects.get(type=Account.Type.REWARD, program=program)
    reward_account.balance = 1
    reward_account.treasury_id = 2
    reward_account.save()
    deposit_wallet = Wallet.objects.create(type=Wallet.Type.DEPOSIT, balance=100, program=program, user=User.objects.get(email=verified_user))
    reward_wallet = Wallet.objects.create(type=Wallet.Type.REWARD, balance=100, program=program, user=User.objects.get(email=verified_user))

    program.reward_currency.custodian_scale = 8
    program.reward_currency.save()

    program = Program.objects.create(slug="".join(choice(string.ascii_letters + string.digits) for x in range(randint(5, 10))), transaction_currency_id=1, reward_currency_id=2, is_enable=True, is_visible=True, begin_date=timezone.now()-timedelta(days=5), emit_duration=timedelta(hours=1), iteration=timedelta(minutes=30))

    deposit_account = Account.objects.get(type=Account.Type.DEPOSIT, program=program)
    deposit_account.balance = 100
    deposit_account.treasury_id = 1
    deposit_account.save()
    reward_account = Account.objects.get(type=Account.Type.REWARD, program=program)
    reward_account.balance = 1
    reward_account.treasury_id = 2
    reward_account.save()
    deposit_wallet = Wallet.objects.create(type=Wallet.Type.DEPOSIT, balance=100, program=program, user=User.objects.get(email=verified_user))
    reward_wallet = Wallet.objects.create(type=Wallet.Type.REWARD, balance=100, program=program, user=User.objects.get(email=verified_user))

    program.reward_currency.custodian_scale = 8
    program.reward_currency.save()

    settings.TREASURY_URL = httpserver.url_for("")[:-1]
    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets/100/transfer/to-main", query_string=f"wallet2={deposit_account.treasury_id}&amount=10").respond_with_json([])
    total_stack_amount_before_stack = deposit_wallet.balance
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.STAKE, program=program)
    Transaction.objects.filter(id=tx.id).update(created_at=program.begin_date)
    assert tx.status == Transaction.Status.SUCCESS

    total_stack_amount_after_stack = Wallet.objects.get(program=program, user__email=verified_user, type=Wallet.Type.DEPOSIT).balance
    assert total_stack_amount_before_stack + 10 == total_stack_amount_after_stack, 'Total stack amount has been changed'

    tasks.calculating_rewards()

    assert Reward.objects.get(program=program, user__email=verified_user).amount == 0.5
    assert Wallet.objects.get(user__email=verified_user, program=program, type=Wallet.Type.REWARD).balance == 100.5


# Approve
def test_create_reward(client, verified_user, httpserver):
    program = Program.objects.create(slug="".join(choice(string.ascii_letters + string.digits) for x in range(randint(5, 10))), transaction_currency_id=1, reward_currency_id=2, is_enable=True, is_visible=True, begin_date=timezone.now()-timedelta(days=5), emit_duration=timedelta(hours=1), iteration=timedelta(minutes=30))

    deposit_account = Account.objects.get(type=Account.Type.DEPOSIT, program=program)
    deposit_account.balance = 100
    deposit_account.treasury_id = 1
    deposit_account.save()
    reward_account = Account.objects.get(type=Account.Type.REWARD, program=program)
    reward_account.balance = 1
    reward_account.treasury_id = 2
    reward_account.save()
    deposit_wallet = Wallet.objects.create(type=Wallet.Type.DEPOSIT, balance=100, program=program, user=User.objects.get(email=verified_user))
    reward_wallet = Wallet.objects.create(type=Wallet.Type.REWARD, balance=100, program=program, user=User.objects.get(email=verified_user))

    program.reward_currency.custodian_scale = 8
    program.reward_currency.save()

    settings.TREASURY_URL = httpserver.url_for("")[:-1]
    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets/100/transfer/to-main", query_string=f"wallet2={deposit_account.treasury_id}&amount=10").respond_with_json([])
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.STAKE, program=program)
    Transaction.objects.filter(id=tx.id).update(created_at=program.begin_date - timedelta(minutes=30))
    assert tx.status == Transaction.Status.SUCCESS

    tasks.calculating_rewards()
    real_reward = Reward.objects.get(program=program, user__email=verified_user)
    real_reward_amount = real_reward.amount
    # Staked half of time
    # (10 / 10) * (1800 / 3600) * 100
    to_reward = 0.5
    assert real_reward_amount == to_reward, 'Reward account balance is not equal to reward computing amount'
    assert Wallet.objects.get(user__email=verified_user, type=Wallet.Type.REWARD).balance == 100.5


# Approve
def test_create_claim_reward(client, verified_user, httpserver):
    program = Program.objects.create(slug="".join(choice(string.ascii_letters + string.digits) for x in range(randint(5, 10))), transaction_currency_id=1, reward_currency_id=2, is_enable=True, is_visible=True, begin_date=timezone.now()-timedelta(days=5), emit_duration=timedelta(hours=1), iteration=timedelta(minutes=30))

    deposit_account = Account.objects.get(type=Account.Type.DEPOSIT, program=program)
    deposit_account.balance = 100
    deposit_account.treasury_id = 1
    deposit_account.save()
    reward_account = Account.objects.get(type=Account.Type.REWARD, program=program)
    reward_account.balance = 1
    reward_account.treasury_id = 2
    reward_account.save()
    deposit_wallet = Wallet.objects.create(type=Wallet.Type.DEPOSIT, balance=100, program=program, user=User.objects.get(email=verified_user))
    reward_wallet = Wallet.objects.create(type=Wallet.Type.REWARD, balance=100, program=program, user=User.objects.get(email=verified_user))

    program.reward_currency.custodian_scale = 8
    program.reward_currency.save()

    settings.TREASURY_URL = httpserver.url_for("")[:-1]
    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets/100/transfer/to-main", query_string=f"wallet2=1&amount=10").respond_with_json([])
    httpserver.expect_request("/wallets/2/transfer/to-main", query_string=f"wallet2=100&amount=0.5").respond_with_json([])
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.STAKE, program=program)
    Transaction.objects.filter(id=tx.id).update(created_at=program.begin_date - timedelta(minutes=30))
    assert tx.status == Transaction.Status.SUCCESS

    tasks.calculating_rewards()
    real_reward = Reward.objects.get(program=program, user__email=verified_user)
    real_reward_amount = real_reward.amount
    assert real_reward_amount == 0.5

    account_balance_before_claim_reward = reward_account.balance
    claim_reward = ClaimReward.objects.create(user=User.objects.get(email=verified_user), program=program, currency_id=1, amount=0.5, wallet=reward_wallet, account=reward_account)
    assert claim_reward.status == ClaimReward.Status.SUCCESS


# Approve
def test_create_stack(client, verified_user, program, deposit_wallet, deposit_account, httpserver):
    settings.TREASURY_URL = httpserver.url_for("")[:-1]
    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets/100/transfer/to-main", query_string=f"wallet2={deposit_account.treasury_id}&amount=10").respond_with_json([])
    account_balance_before_stack = deposit_account.balance
    total_stack_balance_before_stack = deposit_wallet.balance
    transaction = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.STAKE, program=program)
    assert transaction.status == Transaction.Status.SUCCESS

    account = Account.objects.get(program=program, type=Account.Type.DEPOSIT)
    total_stack = Wallet.objects.get(program=program, user__email=verified_user, type=Wallet.Type.DEPOSIT).balance
    assert account.balance == account_balance_before_stack + 10, 'Account balance before stack is not biggest than account balance after stack on amount sum.'
    assert total_stack == total_stack_balance_before_stack + 10, 'Total stack balance before stack is not biggest than total stack balance after stack on amount sum.'


# Approve
def test_create_unstack(client, verified_user, program, deposit_wallet, deposit_account, httpserver):
    settings.TREASURY_URL = httpserver.url_for("")[:-1]
    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request(f"/wallets/{deposit_account.treasury_id}/transfer/to-main", query_string=f"wallet2=100&amount=10").respond_with_json([])
    account_balance_before_unstack = deposit_account.balance
    total_stack_balance_before_unstack = deposit_wallet.balance
    transaction = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.UNSTAKE, program=program)
    assert transaction.status == Transaction.Status.SUCCESS

    account = Account.objects.get(program=program, type=Account.Type.DEPOSIT)
    total_stack = Wallet.objects.get(program=program, user__email=verified_user, type=Wallet.Type.DEPOSIT).balance
    assert account.balance + 10 == account_balance_before_unstack, 'Account balance before unstack is not smaller than account balance after unstack on amount sum.'
    assert total_stack + 10 == total_stack_balance_before_unstack, 'Total stack balance before unstack is not smaller than total stack balance after unstack on amount sum.'


# Approve
def test_create_stack_from_2_users(client, program, deposit_account, httpserver, django_user_model):
    user_1 = django_user_model.objects.create(username="user_1", password="12345")
    deposit_wallet, created = Wallet.objects.get_or_create(user=user_1, type=Wallet.Type.DEPOSIT, program=program)

    settings.TREASURY_URL = httpserver.url_for("")[:-1]

    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user=user_1).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user=user_1).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request(f"/wallets/100/transfer/to-main", query_string=f"wallet2=1&amount=10").respond_with_json([])
    account_balance_before_unstack = Account.objects.get(program=program, type=Account.Type.DEPOSIT).balance
    total_stack_balance_before_unstack = Wallet.objects.get(program=program, user=user_1, type=Wallet.Type.DEPOSIT).balance
    transaction = Transaction.objects.create(user=user_1, currency_id=1, amount=10, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.STAKE, program=program)
    assert transaction.status == Transaction.Status.SUCCESS

    account = Account.objects.get(program=program, type=Account.Type.DEPOSIT)
    total_stack = Wallet.objects.get(program=program, user=user_1, type=Wallet.Type.DEPOSIT).balance
    assert account.balance == account_balance_before_unstack + 10, 'Account balance before unstack is not smaller than account balance after unstack on amount sum.'
    assert total_stack == total_stack_balance_before_unstack + 10, 'Total stack balance before unstack is not smaller than total stack balance after unstack on amount sum.'

    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user=user_1).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user=user_1).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request(f"/wallets/100/transfer/to-main", query_string=f"wallet2=1&amount=15").respond_with_json([])
    account_balance_before_unstack = Account.objects.get(program=program, type=Account.Type.DEPOSIT).balance
    total_stack_balance_before_unstack = Wallet.objects.get(program=program, user=user_1, type=Wallet.Type.DEPOSIT).balance
    transaction = Transaction.objects.create(user=user_1, currency_id=1, amount=15, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.STAKE, program=program)
    assert transaction.status == Transaction.Status.SUCCESS

    account = Account.objects.get(program=program, type=Account.Type.DEPOSIT)
    total_stack = Wallet.objects.get(program=program, user=user_1, type=Wallet.Type.DEPOSIT).balance
    assert account.balance == account_balance_before_unstack + 15, 'Account balance before unstack is not smaller than account balance after unstack on amount sum.'
    assert total_stack == total_stack_balance_before_unstack + 15, 'Total stack balance before unstack is not smaller than total stack balance after unstack on amount sum.'

    user_2 = django_user_model.objects.create(username="user_2", password="12345", email='q@q.q')
    deposit_wallet, created = Wallet.objects.get_or_create(user=user_2, type=Wallet.Type.DEPOSIT, program=program)

    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user=user_2).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 101, "traderId": MainTrader.objects.get(user=user_2).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request(f"/wallets/101/transfer/to-main", query_string=f"wallet2=1&amount=10").respond_with_json([])
    account_balance_before_unstack = Account.objects.get(program=program, type=Account.Type.DEPOSIT).balance
    total_stack_balance_before_unstack = Wallet.objects.get(program=program, user=user_2, type=Wallet.Type.DEPOSIT).balance
    transaction = Transaction.objects.create(user=user_2, currency_id=1, amount=10, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.STAKE, program=program)
    assert transaction.status == Transaction.Status.SUCCESS

    account = Account.objects.get(program=program, type=Account.Type.DEPOSIT)
    total_stack = Wallet.objects.get(program=program, user=user_2, type=Wallet.Type.DEPOSIT).balance
    assert account.balance == account_balance_before_unstack + 10, 'Account balance before unstack is not smaller than account balance after unstack on amount sum.'
    assert total_stack == total_stack_balance_before_unstack + 10, 'Total stack balance before unstack is not smaller than total stack balance after unstack on amount sum.'

    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user=user_2).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 101, "traderId": MainTrader.objects.get(user=user_2).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request(f"/wallets/101/transfer/to-main", query_string=f"wallet2=1&amount=15").respond_with_json([])
    account_balance_before_unstack = Account.objects.get(program=program, type=Account.Type.DEPOSIT).balance
    total_stack_balance_before_unstack = Wallet.objects.get(program=program, user=user_2, type=Wallet.Type.DEPOSIT).balance
    transaction = Transaction.objects.create(user=user_2, currency_id=1, amount=15, wallet=deposit_wallet, account=deposit_account, type=Transaction.Type.STAKE, program=program)
    assert transaction.status == Transaction.Status.SUCCESS

    account = Account.objects.get(program=program, type=Account.Type.DEPOSIT)
    total_stack = Wallet.objects.get(program=program, user=user_2, type=Wallet.Type.DEPOSIT).balance
    assert account.balance == account_balance_before_unstack + 15, 'Account balance before unstack is not smaller than account balance after unstack on amount sum.'
    assert total_stack == total_stack_balance_before_unstack + 15, 'Total stack balance before unstack is not smaller than total stack balance after unstack on amount sum.'


# Approve
def test_create_reward_all_time(client, verified_user, short_program_with_reward, httpserver):
    deposit_wallet, _ = Wallet.objects.get_or_create(user=User.objects.get(email=verified_user), type=Wallet.Type.DEPOSIT, program=short_program_with_reward)
    settings.TREASURY_URL = httpserver.url_for("")[:-1]
    httpserver.expect_request(f"/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets/100/transfer/to-main", query_string=f"wallet2={short_program_with_reward.deposit_account.treasury_id}&amount=10").respond_with_json([])
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10, wallet=deposit_wallet, account=short_program_with_reward.deposit_account, type=Transaction.Type.STAKE, program=short_program_with_reward)
    Transaction.objects.filter(id=tx.id).update(created_at=short_program_with_reward.begin_date - timedelta(minutes=30))
    assert tx.status == Transaction.Status.SUCCESS

    tasks.calculating_rewards()
    real_reward = Reward.objects.get(program=short_program_with_reward, user__email=verified_user)
    real_reward_amount = real_reward.amount
    # Staked half of time
    # (10 / 10) * (1800 / 3600) * 100
    to_reward = 720
    assert real_reward_amount == to_reward, 'Reward account balance is not equal to reward computing amount'
    assert Wallet.objects.get(user__email=verified_user, type=Wallet.Type.REWARD).balance == 720


# Approve
def test_create_reward_half_time(client, verified_user, short_program_with_reward, httpserver):
    deposit_wallet, _ = Wallet.objects.get_or_create(user=User.objects.get(email=verified_user),
                                                     type=Wallet.Type.DEPOSIT, program=short_program_with_reward)
    settings.TREASURY_URL = httpserver.url_for("")[:-1]
    httpserver.expect_request(f"/wallets",
                              query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json(
        [{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id,
          "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4,
                       "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"},
          "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets/100/transfer/to-main",
                              query_string=f"wallet2={short_program_with_reward.deposit_account.treasury_id}&amount=10").respond_with_json(
        [])
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10,
                                    wallet=deposit_wallet, account=short_program_with_reward.deposit_account,
                                    type=Transaction.Type.STAKE, program=short_program_with_reward)
    Transaction.objects.filter(id=tx.id).update(created_at=short_program_with_reward.begin_date + timedelta(minutes=30))
    assert tx.status == Transaction.Status.SUCCESS

    tasks.calculating_rewards()
    real_reward = Reward.objects.get(program=short_program_with_reward, user__email=verified_user)
    real_reward_amount = real_reward.amount
    # Staked half of time
    # (10 / 10) * (1800 / 3600) * 100
    to_reward = 360
    assert real_reward_amount == to_reward, 'Reward account balance is not equal to reward computing amount'
    assert Wallet.objects.get(user__email=verified_user, type=Wallet.Type.REWARD).balance == to_reward


# Approve
def test_create_reward_with_three_tx(client, verified_user, short_program_with_reward, httpserver):
    settings.TREASURY_URL = httpserver.url_for("")[:-1]

    deposit_wallet, _ = Wallet.objects.get_or_create(user=User.objects.get(email=verified_user),
                                                     type=Wallet.Type.DEPOSIT, program=short_program_with_reward)
    httpserver.expect_request(f"/wallets",
                              query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json(
        [{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id,
          "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4,
                       "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"},
          "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets/100/transfer/to-main",
                              query_string=f"wallet2={short_program_with_reward.deposit_account.treasury_id}&amount=10").respond_with_json(
        [])
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10,
                                    wallet=deposit_wallet, account=short_program_with_reward.deposit_account,
                                    type=Transaction.Type.STAKE, program=short_program_with_reward)
    Transaction.objects.filter(id=tx.id).update(created_at=short_program_with_reward.begin_date - timedelta(minutes=30))
    assert tx.status == Transaction.Status.SUCCESS
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10,
                                    wallet=deposit_wallet, account=short_program_with_reward.deposit_account,
                                    type=Transaction.Type.STAKE, program=short_program_with_reward)
    Transaction.objects.filter(id=tx.id).update(created_at=short_program_with_reward.begin_date + timedelta(minutes=30))
    assert tx.status == Transaction.Status.SUCCESS
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10,
                                    wallet=deposit_wallet, account=short_program_with_reward.deposit_account,
                                    type=Transaction.Type.STAKE, program=short_program_with_reward)
    Transaction.objects.filter(id=tx.id).update(created_at=short_program_with_reward.begin_date + timedelta(minutes=45))
    assert tx.status == Transaction.Status.SUCCESS

    tasks.calculating_rewards()

    assert Reward.objects.filter(program=short_program_with_reward, user__email=verified_user).count() == 3
    real_reward_amount = Reward.objects.filter(program=short_program_with_reward, user__email=verified_user).aggregate(amount=Sum('amount'))['amount']
    # Staked half of time
    # (10 / 10) * (1800 / 3600) * 100
    to_reward = 720
    assert real_reward_amount == to_reward, 'Reward account balance is not equal to reward computing amount'
    assert Wallet.objects.get(user__email=verified_user, type=Wallet.Type.REWARD).balance == to_reward


# Approve
def test_create_reward_with_three_tx_2(client, verified_user, short_program_with_reward_30min, httpserver):
    settings.TREASURY_URL = httpserver.url_for("")[:-1]

    deposit_wallet, _ = Wallet.objects.get_or_create(user=User.objects.get(email=verified_user),
                                                     type=Wallet.Type.DEPOSIT, program=short_program_with_reward_30min)
    httpserver.expect_request(f"/wallets",
                              query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json(
        [{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id,
          "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4,
                       "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"},
          "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request(f"/wallets/100/transfer/to-main",
                              query_string=f"wallet2={short_program_with_reward_30min.deposit_account.treasury_id}&amount=10").respond_with_json(
        [])
    httpserver.expect_request(f"/wallets/{short_program_with_reward_30min.reward_account.treasury_id}/transfer/to-main", query_string=f"wallet2=100&amount=360").respond_with_json(
        [])

    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10,
                                    wallet=deposit_wallet, account=short_program_with_reward_30min.deposit_account,
                                    type=Transaction.Type.STAKE, program=short_program_with_reward_30min)
    Transaction.objects.filter(id=tx.id).update(created_at=short_program_with_reward_30min.begin_date - timedelta(minutes=30))
    assert tx.status == Transaction.Status.SUCCESS
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10,
                                    wallet=deposit_wallet, account=short_program_with_reward_30min.deposit_account,
                                    type=Transaction.Type.STAKE, program=short_program_with_reward_30min)
    Transaction.objects.filter(id=tx.id).update(created_at=short_program_with_reward_30min.begin_date + timedelta(minutes=30))
    assert tx.status == Transaction.Status.SUCCESS
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10,
                                    wallet=deposit_wallet, account=short_program_with_reward_30min.deposit_account,
                                    type=Transaction.Type.STAKE, program=short_program_with_reward_30min)
    Transaction.objects.filter(id=tx.id).update(created_at=short_program_with_reward_30min.begin_date + timedelta(minutes=45))
    assert tx.status == Transaction.Status.SUCCESS

    tasks.calculating_rewards()

    tasks.calculating_rewards()

    assert Reward.objects.filter(program=short_program_with_reward_30min, user__email=verified_user).count() == 3
    real_reward_amount = Reward.objects.filter(program=short_program_with_reward_30min, user__email=verified_user).aggregate(amount=Sum('amount'))['amount']
    # Staked half of time
    # (10 / 10) * (1800 / 3600) * 100
    to_reward = 720
    assert real_reward_amount == to_reward, 'Reward account balance is not equal to reward computing amount'
    assert Wallet.objects.get(user__email=verified_user, type=Wallet.Type.REWARD).balance == to_reward


# Approve
def test_create_reward_with_three_tx_2_withclaim(client, verified_user, short_program_with_reward_30min, httpserver):
    settings.TREASURY_URL = httpserver.url_for("")[:-1]

    deposit_wallet, _ = Wallet.objects.get_or_create(user=User.objects.get(email=verified_user),
                                                     type=Wallet.Type.DEPOSIT, program=short_program_with_reward_30min)
    httpserver.expect_request(f"/wallets",
                              query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json(
        [{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id,
          "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4,
                       "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"},
          "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request(f"/wallets/100/transfer/to-main",
                              query_string=f"wallet2={short_program_with_reward_30min.deposit_account.treasury_id}&amount=10").respond_with_json(
        [])
    httpserver.expect_request(f"/wallets/{short_program_with_reward_30min.reward_account.treasury_id}/transfer/to-main", query_string=f"wallet2=100&amount=360").respond_with_json(
        [])

    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10,
                                    wallet=deposit_wallet, account=short_program_with_reward_30min.deposit_account,
                                    type=Transaction.Type.STAKE, program=short_program_with_reward_30min)
    Transaction.objects.filter(id=tx.id).update(created_at=short_program_with_reward_30min.begin_date - timedelta(minutes=30))
    assert tx.status == Transaction.Status.SUCCESS
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10,
                                    wallet=deposit_wallet, account=short_program_with_reward_30min.deposit_account,
                                    type=Transaction.Type.STAKE, program=short_program_with_reward_30min)
    Transaction.objects.filter(id=tx.id).update(created_at=short_program_with_reward_30min.begin_date + timedelta(minutes=30))
    assert tx.status == Transaction.Status.SUCCESS
    tx = Transaction.objects.create(user=User.objects.get(email=verified_user), currency_id=1, amount=10,
                                    wallet=deposit_wallet, account=short_program_with_reward_30min.deposit_account,
                                    type=Transaction.Type.STAKE, program=short_program_with_reward_30min)
    Transaction.objects.filter(id=tx.id).update(created_at=short_program_with_reward_30min.begin_date + timedelta(minutes=45))
    assert tx.status == Transaction.Status.SUCCESS

    tasks.calculating_rewards()

    reward_wallet, _ = Wallet.objects.get_or_create(user=User.objects.get(email=verified_user),
                                       type=Wallet.Type.REWARD, program=short_program_with_reward_30min)

    claim_reward = ClaimReward.objects.create(user=User.objects.get(email=verified_user), program=short_program_with_reward_30min, currency_id=1, amount=360, wallet=reward_wallet, account=short_program_with_reward_30min.reward_account)
    assert claim_reward.status == ClaimReward.Status.SUCCESS

    tasks.calculating_rewards()

    assert Reward.objects.filter(program=short_program_with_reward_30min, user__email=verified_user).count() == 3
    real_reward_amount = Reward.objects.filter(program=short_program_with_reward_30min, user__email=verified_user).aggregate(amount=Sum('amount'))['amount']
    # Staked half of time
    # (10 / 10) * (1800 / 3600) * 100
    to_reward = 720
    assert real_reward_amount == to_reward, 'Reward account balance is not equal to reward computing amount'
    assert Wallet.objects.get(user__email=verified_user, type=Wallet.Type.REWARD).balance == to_reward - 360
