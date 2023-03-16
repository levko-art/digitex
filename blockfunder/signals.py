from blockfunder.models import Transaction, Program
from django.db import DatabaseError
import logging

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


def create_program_accounts(sender, instance: Program, created, **kwargs):
    instance.create_account()
