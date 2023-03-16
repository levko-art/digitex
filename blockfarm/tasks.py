import decimal
import logging

from django.db.models.functions import Coalesce

from common.utils.functional import round_down
from .models import Program, Transaction, Reward, Wallet
from django.utils import timezone
from django.db.models import Sum, Case, When, F, DecimalField
import celery

logger = logging.getLogger(__name__)


@celery.shared_task
def calculating_rewards():
    for program in Program.objects.filter(is_enable=True, begin_date__lt=timezone.now()):
        logger.info(f"Calculating rewards for program {program.id} {program}")

        if program.last_rewarded:
            start_time = program.last_rewarded
        else:
            start_time = program.begin_date
            program.last_rewarded = start_time

        if start_time + program.iteration > timezone.now():
            continue

        total_stack = Transaction.objects.filter(program=program, created_at__lt=start_time, status=Transaction.Status.SUCCESS).aggregate(amount=Coalesce(Sum(Case(When(type=0, then='amount'), When(type=1, then=F('amount') * -1), default=0, output_field=DecimalField())), 0, output_field=DecimalField()))['amount']

        for transaction in Transaction.objects.filter(program=program, created_at__gte=start_time, created_at__lt=start_time + program.iteration, status=Transaction.Status.SUCCESS).order_by('created_at'):
            logger.info(f"Calculating rewards for Transaction {transaction}")
            logger.info(f"\ttotal_stack: {total_stack}")
            duration_between_stack = transaction.created_at - start_time
            logger.info(f"\tduration_between_stack: {duration_between_stack}")

            if total_stack and duration_between_stack:
                for wallet_stacked in Wallet.objects.filter(program=program, type=Wallet.Type.DEPOSIT):
                    logger.info(f"\t\tuser: {wallet_stacked.user.email}")
                    user_total_stack = Transaction.objects.filter(program=program, created_at__lt=transaction.created_at, wallet__user=wallet_stacked.user, status=Transaction.Status.SUCCESS).aggregate(amount=Coalesce(Sum(Case(When(type=Transaction.Type.STAKE, then='amount'), When(type=Transaction.Type.UNSTAKE, then=F('amount') * -1), default=0, output_field=DecimalField())), 0, output_field=DecimalField()))['amount']
                    logger.info(f"\t\tuser_total_stack: {user_total_stack}")
                    if user_total_stack != 0:
                        reward_amount = (user_total_stack / total_stack) * decimal.Decimal(duration_between_stack / program.emit_duration) * program.reward_account.balance
                        reward_amount = round_down(reward_amount, 18)
                        logger.info(f"\t\treward_amount: {reward_amount}")
                        description = f"Rewarded {reward_amount} {program.reward_currency.code} with staked {user_total_stack}/{total_stack} {program.transaction_currency.code} from {start_time} to {transaction.created_at}"
                        created_reward = Reward.objects.create(user=wallet_stacked.user, currency=program.reward_currency, amount=reward_amount, program=program, user_staked=user_total_stack, total_staked=total_stack, duration=duration_between_stack, description=description)

            start_time = transaction.created_at

            if transaction.type == Transaction.Type.STAKE:
                total_stack += transaction.amount

            elif transaction.type == Transaction.Type.UNSTAKE:
                total_stack -= transaction.amount

        program.last_rewarded = program.last_rewarded + program.iteration

        logger.info(f"End of iteration")
        #  Calc end of iterations without transactions
        if total_stack:
            logger.info(f"\ttotal_stack: {total_stack}")
            duration_between_stack = program.last_rewarded - start_time
            logger.info(f"\tduration_between_stack: {duration_between_stack}")

            for wallet_stacked in Wallet.objects.filter(program=program, type=Wallet.Type.DEPOSIT):
                logger.info(f"\t\tuser: {wallet_stacked.user.email}")
                user_total_stack = Transaction.objects.filter(program=program, created_at__lt=program.last_rewarded, wallet__user=wallet_stacked.user, status=Transaction.Status.SUCCESS).aggregate(amount=Coalesce(Sum(Case(When(type=Transaction.Type.STAKE, then='amount'), When(type=Transaction.Type.UNSTAKE, then=F('amount') * -1), default=0, output_field=DecimalField())), 0, output_field=DecimalField()))['amount']
                logger.info(f"\t\tuser_total_stack: {user_total_stack}")
                if user_total_stack != 0:
                    reward_amount = (user_total_stack / total_stack) * decimal.Decimal(duration_between_stack / program.emit_duration) * program.reward_account.balance
                    reward_amount = round_down(reward_amount, program.reward_currency.custodian_scale)
                    logger.info(f"\t\treward_amount: {reward_amount}")
                    description = f"Rewarded {reward_amount} {program.reward_currency.code} with staked {user_total_stack}/{total_stack} {program.transaction_currency.code} from {start_time} to {program.last_rewarded}"
                    created_reward = Reward.objects.create(user=wallet_stacked.user, currency=program.reward_currency, amount=reward_amount, program=program, user_staked=user_total_stack, total_staked=total_stack, duration=duration_between_stack, description=description)

        program.save()


@celery.shared_task
def check_deposit_balance():
    for wallet in Wallet.objects.filter(type=Wallet.Type.DEPOSIT):
        user_total_stack = Transaction.objects.filter(program=wallet.program,
                                                      wallet__user=wallet.user,
                                                      status=Transaction.Status.SUCCESS).aggregate(amount=Coalesce(
            Sum(Case(When(type=Transaction.Type.STAKE, then='amount'),
                     When(type=Transaction.Type.UNSTAKE, then=F('amount') * -1), default=0,
                     output_field=DecimalField())), 0, output_field=DecimalField()))['amount']
        assert wallet.balance == user_total_stack
