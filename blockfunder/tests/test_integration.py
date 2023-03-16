from blockfunder.models import Account, Wallet, Transaction
from django.contrib.auth.models import User
from exchange.models import MainTrader
from django.conf import settings
import logging


logger = logging.getLogger(__name__)

# Tests:
# 1. Normal test
# 2. transaction.amount > program.hard_cap
# 3. transaction.amount > account.balance with buy_out
# 4. transaction.amount > account.balance without buy_out


# Approve
def test_create__transaction_normal(client, verified_user, program, currency_pair_log, httpserver):
    httpserver.expect_request("/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=BTC&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])

    httpserver.expect_request("/wallets/100/swap", query_string="wallet2=1&wallet3=100&wallet4=1&amount1=10&amount2=10.000000000000000000").respond_with_json({'amount1': 10, 'amount2': 10}, status=200)

    settings.TREASURY_URL = httpserver.url_for("")[:-1]

    deposit_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)
    deposit_account_before_transaction.treasury_id = 1
    deposit_account_before_transaction.balance = 20
    deposit_account_before_transaction.save()

    reward_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)
    reward_account_before_transaction.treasury_id = 1
    reward_account_before_transaction.balance = 1000000
    reward_account_before_transaction.save()

    deposit_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)
    deposit_wallet_before_transaction.balance = 1000000000
    deposit_wallet_before_transaction.save()

    reward_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)
    reward_wallet_before_transaction.balance = 38
    reward_wallet_before_transaction.save()

    transaction = Transaction.objects.create(program=program,
                                             amount=10,
                                             deposit_account=Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)[0],
                                             reward_account=Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)[0],
                                             deposit_currency_id=1,
                                             deposit_wallet=Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)[0],
                                             reward_wallet=Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)[0],
                                             user=User.objects.get(email=verified_user))

    assert transaction.status == Transaction.Status.SUCCESS
    assert Wallet.objects.get(id=reward_wallet_before_transaction.id).total_rewarded == 10

    deposit_account_after_transaction = Account.objects.get(type=Account.Type.DEPOSIT, program=program, currency_id=1)
    reward_account_after_transaction = Account.objects.get(type=Account.Type.REWARD, program=program, currency_id=2)
    deposit_wallet_after_transaction = Wallet.objects.get(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)
    reward_wallet_after_transaction = Wallet.objects.get(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)

    assert deposit_account_before_transaction.balance + 10 == deposit_account_after_transaction.balance, 'Unexpected value in deposit account'
    assert deposit_wallet_before_transaction.balance == deposit_wallet_after_transaction.balance + 10, 'Unexpected value in deposit wallet'
    assert reward_account_before_transaction.balance == reward_account_after_transaction.balance + 10, 'Unexpected value in reward account'
    assert reward_wallet_before_transaction.balance + 10 == reward_wallet_after_transaction.balance, 'Unexpected value in reward wallet'


# Approve
def test_create_transaction__transaction_amount_gte_program_hard_cap(client, verified_user, program, currency_pair_log, httpserver):
    deposit_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)
    deposit_account_before_transaction.treasury_id = 1
    deposit_account_before_transaction.balance = 20
    deposit_account_before_transaction.save()

    reward_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)
    reward_account_before_transaction.treasury_id = 1
    reward_account_before_transaction.balance = 1000000
    reward_account_before_transaction.save()

    deposit_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)
    deposit_wallet_before_transaction.balance = 1000000000
    deposit_wallet_before_transaction.save()

    reward_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)
    reward_wallet_before_transaction.balance = 38
    reward_wallet_before_transaction.save()

    transaction = Transaction.objects.create(program=program,
                                             amount=101,
                                             deposit_account=Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)[0],
                                             reward_account=Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)[0],
                                             deposit_currency_id=1,
                                             deposit_wallet=Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)[0],
                                             reward_wallet=Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)[0],
                                             user=User.objects.get(email=verified_user))

    assert transaction.status == Transaction.Status.FAILED
    assert Wallet.objects.get(id=reward_wallet_before_transaction.id).total_rewarded == 0

    deposit_account_after_transaction = Account.objects.get(type=Account.Type.DEPOSIT, program=program, currency_id=1)
    reward_account_after_transaction = Account.objects.get(type=Account.Type.REWARD, program=program, currency_id=2)
    deposit_wallet_after_transaction = Wallet.objects.get(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)
    reward_wallet_after_transaction = Wallet.objects.get(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)

    assert deposit_account_before_transaction.balance == deposit_account_after_transaction.balance, 'Unexpected value in deposit account'
    assert deposit_wallet_before_transaction.balance == deposit_wallet_after_transaction.balance, 'Unexpected value in deposit wallet'
    assert reward_account_before_transaction.balance == reward_account_after_transaction.balance, 'Unexpected value in reward account'
    assert reward_wallet_before_transaction.balance == reward_wallet_after_transaction.balance, 'Unexpected value in reward wallet'


# Approve
def test_create_transaction__transaction_amount_gte_account_balance_without_buy_out(client, verified_user, program, currency_pair_log, httpserver):
    httpserver.expect_request("/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=BTC&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])

    httpserver.expect_request("/wallets/100/swap", query_string="wallet2=1&wallet3=1&wallet4=100&amount1=10&amount2=10.000000000000000000").respond_with_json({'message': 'error'}, status=400)

    settings.TREASURY_URL = httpserver.url_for("")[:-1]

    deposit_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)
    deposit_account_before_transaction.treasury_id = 1
    deposit_account_before_transaction.balance = 20
    deposit_account_before_transaction.save()

    reward_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)
    reward_account_before_transaction.treasury_id = 1
    reward_account_before_transaction.balance = 5
    reward_account_before_transaction.save()

    deposit_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)
    deposit_wallet_before_transaction.balance = 1000000000
    deposit_wallet_before_transaction.save()

    reward_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)
    reward_wallet_before_transaction.balance = 38
    reward_wallet_before_transaction.save()

    transaction = Transaction.objects.create(program=program,
                                             amount=10,
                                             deposit_account=Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)[0],
                                             reward_account=Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)[0],
                                             deposit_currency_id=1,
                                             deposit_wallet=Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)[0],
                                             reward_wallet=Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)[0],
                                             user=User.objects.get(email=verified_user),
                                             buy_out=False)

    assert transaction.status == Transaction.Status.FAILED
    assert Wallet.objects.get(id=reward_wallet_before_transaction.id).total_rewarded == 0

    deposit_account_after_transaction = Account.objects.get(type=Account.Type.DEPOSIT, program=program, currency_id=1)
    reward_account_after_transaction = Account.objects.get(type=Account.Type.REWARD, program=program, currency_id=2)
    deposit_wallet_after_transaction = Wallet.objects.get(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)
    reward_wallet_after_transaction = Wallet.objects.get(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)

    assert deposit_account_before_transaction.balance == deposit_account_after_transaction.balance, 'Unexpected value in deposit account'
    assert deposit_wallet_before_transaction.balance == deposit_wallet_after_transaction.balance, 'Unexpected value in deposit wallet'
    assert reward_account_before_transaction.balance == reward_account_after_transaction.balance, 'Unexpected value in reward account'
    assert reward_wallet_before_transaction.balance == reward_wallet_after_transaction.balance, 'Unexpected value in reward wallet'


# Approve
def test_create_transaction__transaction_amount_gte_account_balance_with_buy_out(client, verified_user, program, currency_pair_log, httpserver):
    httpserver.expect_request("/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=BTC&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])

    httpserver.expect_request("/wallets/100/swap", query_string="wallet2=1&wallet3=100&wallet4=1&amount1=10&amount2=10.000000000000000000&buyout=True").respond_with_json({'amount1': 5, 'amount2': 5}, status=200)

    settings.TREASURY_URL = httpserver.url_for("")[:-1]

    deposit_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)
    deposit_account_before_transaction.treasury_id = 1
    deposit_account_before_transaction.balance = 20
    deposit_account_before_transaction.save()

    reward_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)
    reward_account_before_transaction.treasury_id = 1
    reward_account_before_transaction.balance = 5
    reward_account_before_transaction.save()

    deposit_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)
    deposit_wallet_before_transaction.balance = 1000000000
    deposit_wallet_before_transaction.save()

    reward_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)
    reward_wallet_before_transaction.balance = 38
    reward_wallet_before_transaction.save()

    transaction = Transaction.objects.create(program=program,
                                             amount=10,
                                             deposit_account=Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)[0],
                                             reward_account=Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)[0],
                                             deposit_currency_id=1,
                                             deposit_wallet=Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)[0],
                                             reward_wallet=Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)[0],
                                             user=User.objects.get(email=verified_user),
                                             buy_out=True)

    assert transaction.status == Transaction.Status.SUCCESS
    assert Wallet.objects.get(id=reward_wallet_before_transaction.id).total_rewarded == 5

    deposit_account_after_transaction = Account.objects.get(type=Account.Type.DEPOSIT, program=program, currency_id=1)
    reward_account_after_transaction = Account.objects.get(type=Account.Type.REWARD, program=program, currency_id=2)
    deposit_wallet_after_transaction = Wallet.objects.get(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)
    reward_wallet_after_transaction = Wallet.objects.get(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)

    assert deposit_account_before_transaction.balance + 5 == deposit_account_after_transaction.balance, 'Unexpected value in deposit account'
    assert deposit_wallet_before_transaction.balance == deposit_wallet_after_transaction.balance + 5, 'Unexpected value in deposit wallet'
    assert reward_account_before_transaction.balance == reward_account_after_transaction.balance + 5, 'Unexpected value in reward account'
    assert reward_wallet_before_transaction.balance + 5 == reward_wallet_after_transaction.balance, 'Unexpected value in reward wallet'


# Approve
def test_create_transaction__transaction_amount_gte_account_balance_with_buy_out_error(client, verified_user, program, currency_pair_log, httpserver):
    httpserver.expect_request("/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=BTC&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])

    httpserver.expect_request("/wallets/100/swap", query_string="wallet2=1&wallet3=1&wallet4=100&amount1=10&amount2=10.000000000000000000&buyout=True").respond_with_json({'message': 'error'}, status=400)

    settings.TREASURY_URL = httpserver.url_for("")[:-1]

    deposit_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)
    deposit_account_before_transaction.treasury_id = 1
    deposit_account_before_transaction.balance = 20
    deposit_account_before_transaction.save()

    reward_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)
    reward_account_before_transaction.treasury_id = 1
    reward_account_before_transaction.balance = 5
    reward_account_before_transaction.save()

    deposit_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)
    deposit_wallet_before_transaction.balance = 1000000000
    deposit_wallet_before_transaction.save()

    reward_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)
    reward_wallet_before_transaction.balance = 38
    reward_wallet_before_transaction.save()

    transaction = Transaction.objects.create(program=program,
                                             amount=10,
                                             deposit_account=Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)[0],
                                             reward_account=Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)[0],
                                             deposit_currency_id=1,
                                             deposit_wallet=Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)[0],
                                             reward_wallet=Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)[0],
                                             user=User.objects.get(email=verified_user),
                                             buy_out=True)

    assert transaction.status == Transaction.Status.FAILED
    assert Wallet.objects.get(id=reward_wallet_before_transaction.id).total_rewarded == 0

    deposit_account_after_transaction = Account.objects.get(type=Account.Type.DEPOSIT, program=program, currency_id=1)
    reward_account_after_transaction = Account.objects.get(type=Account.Type.REWARD, program=program, currency_id=2)
    deposit_wallet_after_transaction = Wallet.objects.get(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)
    reward_wallet_after_transaction = Wallet.objects.get(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)

    assert deposit_account_before_transaction.balance == deposit_account_after_transaction.balance, 'Unexpected value in deposit account'
    assert deposit_wallet_before_transaction.balance == deposit_wallet_after_transaction.balance, 'Unexpected value in deposit wallet'
    assert reward_account_before_transaction.balance == reward_account_after_transaction.balance, 'Unexpected value in reward account'
    assert reward_wallet_before_transaction.balance == reward_wallet_after_transaction.balance, 'Unexpected value in reward wallet'


def test_create__transaction_normal_2_transactions(client, verified_user, program, currency_pair_log, httpserver):
    httpserver.expect_request("/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=DGTX&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])
    httpserver.expect_request("/wallets", query_string=f"traderId={MainTrader.objects.get(user__email=verified_user).trader_id}&currencyCode=BTC&kind=DEPOSIT").respond_with_json([{"id": 100, "traderId": MainTrader.objects.get(user__email=verified_user).trader_id, "currency": {"id": 1, "currencyPairId": 0, "name": "Digitex", "code": "DGTX", "scale": 4, "sellPrice": "1.00000000000000000000", "buyPrice": "1.00000000000000000000"}, "balance": "10000.00000000000000000000", "blockchainAddress": "0x0A190CE3Ba33e0D2c999f35E58AF1202b064fe2F"}])

    httpserver.expect_request("/wallets/100/swap", query_string="wallet2=1&wallet3=100&wallet4=1&amount1=10&amount2=10.000000000000000000").respond_with_json({'amount1': 10, 'amount2': 10}, status=200)
    httpserver.expect_request("/wallets/100/swap", query_string="wallet2=1&wallet3=100&wallet4=1&amount1=9&amount2=9.000000000000000000").respond_with_json({'amount1': 9, 'amount2': 9}, status=200)

    settings.TREASURY_URL = httpserver.url_for("")[:-1]

    deposit_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)
    deposit_account_before_transaction.treasury_id = 1
    deposit_account_before_transaction.balance = 20
    deposit_account_before_transaction.save()

    reward_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)
    reward_account_before_transaction.treasury_id = 1
    reward_account_before_transaction.balance = 1000000
    reward_account_before_transaction.save()

    deposit_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)
    deposit_wallet_before_transaction.balance = 1000000000
    deposit_wallet_before_transaction.save()

    reward_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)
    reward_wallet_before_transaction.balance = 38
    reward_wallet_before_transaction.save()

    transaction = Transaction.objects.create(program=program,
                                             amount=10,
                                             deposit_account=Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)[0],
                                             reward_account=Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)[0],
                                             deposit_currency_id=1,
                                             deposit_wallet=Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)[0],
                                             reward_wallet=Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)[0],
                                             user=User.objects.get(email=verified_user))

    assert transaction.status == Transaction.Status.SUCCESS
    assert Wallet.objects.get(id=reward_wallet_before_transaction.id).total_rewarded == 10

    deposit_account_after_transaction = Account.objects.get(type=Account.Type.DEPOSIT, program=program, currency_id=1)
    reward_account_after_transaction = Account.objects.get(type=Account.Type.REWARD, program=program, currency_id=2)
    deposit_wallet_after_transaction = Wallet.objects.get(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)
    reward_wallet_after_transaction = Wallet.objects.get(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)

    assert deposit_account_before_transaction.balance + 10 == deposit_account_after_transaction.balance, 'Unexpected value in deposit account'
    assert deposit_wallet_before_transaction.balance == deposit_wallet_after_transaction.balance + 10, 'Unexpected value in deposit wallet'
    assert reward_account_before_transaction.balance == reward_account_after_transaction.balance + 10, 'Unexpected value in reward account'
    assert reward_wallet_before_transaction.balance + 10 == reward_wallet_after_transaction.balance, 'Unexpected value in reward wallet'

    deposit_account_before_2_transaction = Account.objects.get(id=deposit_account_before_transaction.id)
    reward_account_before_2_transaction = Account.objects.get(id=reward_account_before_transaction.id)
    deposit_wallet_before_2_transaction = Wallet.objects.get(id=deposit_wallet_before_transaction.id)
    reward_wallet_before_2_transaction = Wallet.objects.get(id=reward_wallet_before_transaction.id)

    transaction_2 = Transaction.objects.create(program=program,
                                             amount=9,
                                             deposit_account=Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)[0],
                                             reward_account=Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)[0],
                                             deposit_currency_id=1,
                                             deposit_wallet=Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)[0],
                                             reward_wallet=Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)[0],
                                             user=User.objects.get(email=verified_user))

    assert transaction_2.status == Transaction.Status.SUCCESS
    assert Wallet.objects.get(id=reward_wallet_before_2_transaction.id).total_rewarded == 19

    deposit_account_after_2_transaction = Account.objects.get(id=deposit_account_after_transaction.id)
    reward_account_after_2_transaction = Account.objects.get(id=reward_account_after_transaction.id)
    deposit_wallet_after_2_transaction = Wallet.objects.get(id=deposit_wallet_after_transaction.id)
    reward_wallet_after_2_transaction = Wallet.objects.get(id=reward_wallet_after_transaction.id)

    assert deposit_account_before_2_transaction.balance + 9 == deposit_account_after_2_transaction.balance, 'Unexpected value in deposit account'
    assert deposit_wallet_before_2_transaction.balance == deposit_wallet_after_2_transaction.balance + 9, 'Unexpected value in deposit wallet'
    assert reward_account_before_2_transaction.balance == reward_account_after_2_transaction.balance + 9, 'Unexpected value in reward account'
    assert reward_wallet_before_2_transaction.balance + 9 == reward_wallet_after_2_transaction.balance, 'Unexpected value in reward wallet'
