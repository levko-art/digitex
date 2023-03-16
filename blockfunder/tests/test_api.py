import logging
from django.contrib.auth.models import User
from rest_framework import status
from blockfunder.models import *
import decimal

logger = logging.getLogger(__name__)


# Approve
def test_list_of_programs(client, verified_user, program):
    response = client.get(f'/dapi/blockfunder/program/')
    assert response.status_code == status.HTTP_200_OK, response.data


# Approve
def test_get_program_by_id(client, verified_user, program):
    response = client.get(f'/dapi/blockfunder/program/{program.id}/')
    assert response.status_code == status.HTTP_200_OK, response.data


# Approve
def test_list_transaction(verified_client, verified_user, program):
    Transaction.objects.create(program=program,
                               amount=10,
                               deposit_account=Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=program, currency_id=1)[0],
                               reward_account=Account.objects.get_or_create(type=Account.Type.REWARD, program=program, currency_id=2)[0],
                               deposit_currency_id=1,
                               deposit_wallet=Wallet.objects.get_or_create(type=Wallet.Type.DEPOSIT, user=User.objects.get(email=verified_user), program=program)[0],
                               reward_wallet=Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=User.objects.get(email=verified_user), program=program)[0],
                               user=User.objects.get(email=verified_user))
    response = verified_client.get(f'/dapi/blockfunder/program/{program.id}/transaction/')
    assert response.status_code == status.HTTP_200_OK, response.data


# Approve
def test_create_transaction(verified_client, verified_user, program):
    request = {
        'amount': 10,
        'currency_code': 'DGTX'
    }
    response = verified_client.post(f'/dapi/blockfunder/program/{program.id}/transaction/', request, format='json')
    assert response.status_code == status.HTTP_201_CREATED, response.data


# Approve
def test_create_transaction__false_program_buy_enable(verified_client, verified_user):
    program, created = Program.objects.get_or_create(reward_currency_id=2, is_enable=True, is_visible=True, rate=decimal.Decimal(10.0), hard_cap=decimal.Decimal(100.0), buy_enable=False)

    request = {
        'amount': 10,
        'currency_code': 'DGTX'
    }
    response = verified_client.post(f'/dapi/blockfunder/program/{program.id}/transaction/', request, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
