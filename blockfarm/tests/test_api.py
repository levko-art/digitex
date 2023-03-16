import logging

from rest_framework import status
from django.urls import reverse

logger = logging.getLogger(__name__)


# +
def test_list_of_programs(client, verified_user, program):
    response = client.get(f'/dapi/blockfarm/program/')
    assert response.status_code == status.HTTP_200_OK, response.data


# +
def test_get_program_by_id(client, verified_user, program):
    response = client.get(f'/dapi/blockfarm/program/{program.id}/')
    assert response.status_code == status.HTTP_200_OK, response.data


# +
def test_list_of_rewards_by_user(verified_client, verified_user, program):
    response = verified_client.get(f'/dapi/blockfarm/program/{program.id}/reward/')
    assert response.status_code == status.HTTP_200_OK, response.data


# +
def test_list_transaction(verified_client, verified_user, program):
    response = verified_client.get(f'/dapi/blockfarm/program/{program.id}/transaction/')
    assert response.status_code == status.HTTP_200_OK, response.data


# +
def test_create_stack(verified_client, verified_user, program, deposit_wallet, deposit_account):
    request = {
        'currency_code': 'BTC',
        'amount': 10,
        'type': 0,
        'program': program.id
    }
    response = verified_client.post(f'/dapi/blockfarm/program/{program.id}/transaction/', request, format='json')
    assert response.status_code == status.HTTP_201_CREATED, response.data


# +
def test_create_unstack(verified_client, verified_user, program, deposit_wallet, deposit_account):
    request = {
        'currency_code': 'BTC',
        'amount': 10,
        'type': 1,
        'program': program.id
    }
    response = verified_client.post(f'/dapi/blockfarm/program/{program.id}/transaction/', request, format='json')
    assert response.status_code == status.HTTP_201_CREATED, response.data


# +
def test_list_claim_reward(verified_client, verified_user, program):
    response = verified_client.get(f'/dapi/blockfarm/program/{program.id}/claim_reward/')
    assert response.status_code == status.HTTP_200_OK, response.data


# +
def test_create_claim_reward(verified_client, verified_user, program, deposit_wallet, reward_wallet, deposit_account, reward_account):
    program.claim_enabled = True
    program.save()

    request = {
        'amount': 10,
    }
    reward_account.balance = 10
    reward_account.save()
    reward_wallet.balance = 10
    reward_wallet.save()
    response = verified_client.post(f'/dapi/blockfarm/program/{program.id}/claim_reward/', request, format='json')
    assert response.status_code == status.HTTP_201_CREATED, response.data


def test_create_claim_reward_not_allowed(verified_client, verified_user, program, deposit_wallet, reward_wallet, deposit_account, reward_account):
    request = {
        'amount': 10,
    }
    reward_account.balance = 10
    reward_account.save()
    reward_wallet.balance = 10
    reward_wallet.save()
    response = verified_client.post(f'/dapi/blockfarm/program/{program.id}/claim_reward/', request, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data


# +
def test_get_reward_status_by_user_and_program(verified_client, verified_user, program):
    response = verified_client.get(f'/dapi/blockfarm/program/{program.id}/reward_status/')
    assert response.status_code == status.HTTP_200_OK, response.data
