import logging
from django.db import DatabaseError

from blockfarm.models import Transaction, ClaimReward, Program, Reward

logger = logging.getLogger(__name__)


def push_transaction(sender, instance: Transaction, created, **kwargs):
    if created:
        try:
            instance.create_transaction()
            logger.debug('create_transaction() success')
        except (DatabaseError, Exception) as exception:
            logger.error(f'create_transaction() failed, exception ({exception})')
            instance.status = Transaction.Status.FAILED
            instance.save()


def push_claim_reward(sender, instance: ClaimReward, created, **kwargs):
    if created:

        try:
            instance.create_claim_reward()
            logger.debug('create_create_claim_reward() success')

        except (DatabaseError, Exception) as exception:
            logger.error(f'create_create_claim_reward() failed, exception ({exception})')
            instance.status = ClaimReward.Status.FAILED
            instance.save()


def push_reward(sender, instance: Reward, created, **kwargs):
    if created:
        try:
            instance.update_wallet()
            logger.debug('create_transaction() success')
        except (DatabaseError, Exception) as exception:
            logger.error(f'create_transaction() failed, exception ({exception})')


def create_program_accounts(sender, instance: Program, created, **kwargs):
    if created:
        instance.create_account()
