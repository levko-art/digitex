import json
from uuid import UUID

import pytest
from django.contrib.auth.models import User

from blockfunder.models import Transaction, Account, Wallet
from blockfunder.serializers import TransactionSerializer
from exchange.serializers import CurrencySerializer


def transaction(program, verified_user) -> Transaction:
    deposit_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.DEPOSIT,
                                                                                program=program, currency_id=1)
    deposit_account_before_transaction.treasury_id = 1
    deposit_account_before_transaction.balance = 20
    deposit_account_before_transaction.save()

    reward_account_before_transaction, created = Account.objects.get_or_create(type=Account.Type.REWARD,
                                                                               program=program, currency_id=2)
    reward_account_before_transaction.treasury_id = 1
    reward_account_before_transaction.balance = 1000000
    reward_account_before_transaction.save()

    deposit_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT,
                                                                              user=User.objects.get(
                                                                                  email=verified_user), program=program)
    deposit_wallet_before_transaction.balance = 1000000000
    deposit_wallet_before_transaction.save()

    reward_wallet_before_transaction, created = Wallet.objects.get_or_create(type=Wallet.Type.REWARD,
                                                                             user=User.objects.get(email=verified_user),
                                                                             program=program)
    reward_wallet_before_transaction.balance = 38
    reward_wallet_before_transaction.save()

    transaction = Transaction.objects.create(program=program,
                                             amount=101,
                                             deposit_account=
                                             Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program,
                                                                           currency_id=1)[0],
                                             reward_account=
                                             Account.objects.get_or_create(type=Account.Type.REWARD, program=program,
                                                                           currency_id=2)[0],
                                             deposit_currency_id=1,
                                             deposit_wallet=Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT,
                                                                                         user=User.objects.get(
                                                                                             email=verified_user),
                                                                                         program=program)[0],
                                             reward_wallet=Wallet.objects.get_or_create(type=Wallet.Type.REWARD,
                                                                                        user=User.objects.get(
                                                                                            email=verified_user),
                                                                                        program=program)[0],
                                             user=User.objects.get(email=verified_user))
    return transaction


@pytest.mark.skip(reason="no way of currently testing asserts with serializer.data")
def test_transaction_serialize(program, verified_user):
    tx: Transaction = transaction(program, verified_user)

    serializer = TransactionSerializer(tx)

    deposit_currency_serializer = CurrencySerializer(tx.deposit_currency)
    reward_currency_serializer = CurrencySerializer(tx.program.reward_currency)

    assert serializer.data == {'amount': '101.000000000000000000', 'created_at': str(tx.created_at),
                               'deposit_currency': deposit_currency_serializer.data,
                               'reward_currency': reward_currency_serializer.data,
                               'id': str(tx.id),
                               'program': str(program.id), 'status': 3}
