import decimal
from datetime import timedelta

from django.contrib.auth.models import User
from django.core import validators
from django.db.models import F, Max, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property

from common.helpers import TreasuryAPI
from django.db import models, transaction
from exchange import fields
import uuid

from exchange.models import MainTrader

__all__ = 'Program', 'Account', 'Transaction', 'Reward', 'ClaimReward', 'ProgramLink', 'Wallet'


class Account(models.Model):
    class Type:
        DEPOSIT = 0
        REWARD = 1

        CHOICES = [
            (DEPOSIT, 'Deposit wallet'),
            (REWARD, 'Reward wallet'),
        ]

        _default_value, _name = CHOICES[0]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    type = models.IntegerField(choices=Type.CHOICES)
    program = models.ForeignKey('Program', models.PROTECT)
    currency = models.ForeignKey('exchange.Currency', models.PROTECT, related_name='+')
    balance = fields.FixedDecimalField(default=0.0, validators=[validators.MinValueValidator(limit_value=0)])
    treasury_id = models.IntegerField(null=True)

    def __str__(self):
        return f'Account #{self.id}, Program: {self.program}.'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['type', 'program'], name='unique_account'),
            models.CheckConstraint(check=models.Q(balance__gte=0), name='balance_gte_0')
        ]


class Program(models.Model):

    def _end_date(self):
        if self.begin_date and self.emit_duration:
            result = self.begin_date + self.emit_duration
            return result
        else:
            return None

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=128, default='')
    slug = models.SlugField(max_length=64, unique=True, null=False, blank=False)
    transaction_currency = models.ForeignKey('exchange.Currency', on_delete=models.PROTECT, related_name='+')
    reward_currency = models.ForeignKey('exchange.Currency', on_delete=models.PROTECT, related_name='+')
    emit_duration = models.DurationField(null=True, blank=True)
    begin_date = models.DateTimeField(null=True, blank=True)
    end_date = property(_end_date)
    prestake_date = models.DateTimeField(null=True, blank=True, help_text="Date of prestake opens")
    iteration = models.DurationField(default=timedelta(hours=1))
    is_enable = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=False)
    last_rewarded = models.DateTimeField(blank=True, null=True)
    links = models.ManyToManyField('ProgramLink', blank=True)

    claim_enabled = models.BooleanField(default=False)
    stack_enabled = models.BooleanField(default=False)
    unstack_enabled = models.BooleanField(default=False)

    def create_account(self):
        Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=self, currency=self.transaction_currency)
        Account.objects.get_or_create(type=Account.Type.REWARD, program=self, currency=self.reward_currency)

    @property
    def deposit_account(self) -> Account:
        return Account.objects.get(type=Account.Type.DEPOSIT, program=self)

    @property
    def reward_account(self) -> Account:
        return Account.objects.get(type=Account.Type.REWARD, program=self)

    @property
    def total_staked(self) -> decimal.Decimal:
        """
        Current Total tokens staked by users of program

        :return: decimal.Decimal as tokens amount
        """
        return self.deposit_account.balance

    @property
    def total_rewards(self) -> decimal.Decimal:
        """
        Current Total reward of program

        :return: decimal.Decimal as tokens amount
        """
        return self.reward_account.balance

    @property
    def participants(self) -> int:
        return self.wallet_set.filter(type=Wallet.Type.DEPOSIT, balance__gt=0).count()

    @property
    def apy(self) -> decimal.Decimal:
        """
        Current APY of program

        :return: decimal.Decimal as percentage
        """
        if self.deposit_account.balance * self.transaction_currency.usd_rate == 0:
            apy = 1000
        else:
            apy = pow(1 + ((self.reward_account.balance * self.reward_currency.usd_rate) / (self.deposit_account.balance * self.transaction_currency.usd_rate)) * decimal.Decimal((self.emit_duration / timedelta(days=30))), 12) - 1
            if apy > 1000:
                apy = 1000
        return apy

    @cached_property
    def max_participants(self):
        return Transaction.objects.filter(program=self.id).order_by('user').distinct('user').count()

    @cached_property
    def max_staked(self):
        return Reward.objects.filter(program=self.id).aggregate(total_staked=Coalesce(Max('total_staked'), Value(0, output_field=DecimalField())))['total_staked']

    @cached_property
    def max_apy(self):
        if self.max_staked * self.transaction_currency.usd_rate == 0:
            apy = 1000
        else:
            apy = pow(1 + ((self.reward_account.balance * self.reward_currency.usd_rate) / (self.max_staked * self.transaction_currency.usd_rate)) * decimal.Decimal((self.emit_duration / timedelta(days=30))), 12) - 1
            if apy > 1000:
                apy = 1000
        return apy

    class Meta:
        ordering = [F('begin_date').asc(nulls_last=True)]

    def __str__(self):
        return f'Program #{self.id}.'


class ProgramLink(models.Model):
    name = models.CharField(max_length=128)
    hyperlink = models.CharField(max_length=512)


class Wallet(models.Model):
    class Type:
        DEPOSIT = 0
        REWARD = 1

        CHOICES = [
            (DEPOSIT, 'Deposit wallet'),
            (REWARD, 'Reward wallet'),
        ]

        _default_value, _name = CHOICES[0]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    type = models.IntegerField(choices=Type.CHOICES)
    user = models.ForeignKey(User, models.PROTECT, null=False, blank=False)
    balance = fields.FixedDecimalField(default=0, validators=[validators.MinValueValidator(limit_value=0)])
    program = models.ForeignKey(Program, models.PROTECT, null=False, blank=False)

    def get_wallet(self, currency_code):
        trader = MainTrader.objects.get(user=self.user)
        return trader.get_wallet(currency_code)

    def __str__(self):
        return f'Wallet #{self.id}, User: {self.user}.'

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(balance__gte=0), name='balance_gte_0'),
            models.UniqueConstraint(fields=['type', 'user', 'program'], name='unique_wallet')
        ]


class Transaction(models.Model):
    class Type:
        STAKE = 0
        UNSTAKE = 1

        CHOICES = [
            (STAKE, 'Stake'),
            (UNSTAKE, 'Unstake'),
        ]

        _default_value, _name = CHOICES[0]

    class Status:
        UNDEFINED = 0
        PENDING = 1
        SUCCESS = 2
        FAILED = 3

        CHOICES = [
            (UNDEFINED, 'Undefined'),
            (PENDING, 'Pending'),
            (SUCCESS, 'Success'),
            (FAILED, 'Failed'),
        ]

        _default_value, _name = CHOICES[0]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    user = models.ForeignKey(User, models.PROTECT)
    currency = models.ForeignKey('exchange.Currency', models.PROTECT, related_name='+')
    amount = fields.FixedDecimalField(validators=[validators.MinValueValidator(limit_value=0)])
    wallet = models.ForeignKey('Wallet', models.PROTECT)
    account = models.ForeignKey('Account', models.PROTECT)
    created_at = models.DateTimeField(auto_now=True)
    type = models.IntegerField(choices=Type.CHOICES)
    status = models.IntegerField(choices=Status.CHOICES, default=Status.UNDEFINED)
    program = models.ForeignKey('Program', models.PROTECT)
    rewarded = models.BooleanField(default=False)

    def create_transaction(self):
        if self.type == Transaction.Type.STAKE:
            TreasuryAPI().treasury_wallet_controller().transfer_to_main(self.wallet.get_wallet(self.program.transaction_currency.code).id, self.account.treasury_id, str(self.amount))
            with transaction.atomic():
                Account.objects.filter(id=self.account_id).update(balance=F("balance") + self.amount)
                Wallet.objects.filter(id=self.wallet_id).update(balance=F("balance") + self.amount)
        elif self.type == Transaction.Type.UNSTAKE:
            with transaction.atomic():
                Account.objects.filter(id=self.account_id).update(balance=F("balance") - self.amount)
                Wallet.objects.filter(id=self.wallet_id).update(balance=F("balance") - self.amount)
            TreasuryAPI().treasury_wallet_controller().transfer_to_main(self.account.treasury_id, self.wallet.get_wallet(self.program.transaction_currency.code).id, str(self.amount))
        else:
            raise NotImplementedError(f'Transaction type {self.type} not implemented')

        self.status = Transaction.Status.SUCCESS
        self.save()

    class Meta:
        ordering = ['-created_at', 'id']
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gte=0), name='amount_gte_0')
        ]

    def __str__(self):
        return f'Transaction #{self.id}.'


class Reward(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    user = models.ForeignKey(User, models.PROTECT)
    program = models.ForeignKey('Program', models.PROTECT)
    currency = models.ForeignKey('exchange.Currency', models.PROTECT, related_name='+')
    amount = fields.FixedDecimalField(validators=[validators.MinValueValidator(limit_value=0)])
    user_staked = fields.FixedDecimalField(validators=[validators.MinValueValidator(limit_value=0)])
    total_staked = fields.FixedDecimalField(validators=[validators.MinValueValidator(limit_value=0)])
    duration = models.DurationField()
    description = models.CharField(max_length=512, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', 'id']
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gte=0), name='amount_gte_0')
        ]

    def __str__(self):
        return f'Reward #{self.id}.'

    def update_wallet(self):
        Wallet.objects.get_or_create(type=Wallet.Type.REWARD, user=self.user, program=self.program)
        Wallet.objects.filter(type=Wallet.Type.REWARD, user=self.user, program=self.program).update(balance=F("balance") + self.amount)


class ClaimReward(models.Model):
    class Status:
        UNDEFINED = 0
        PENDING = 1
        SUCCESS = 2
        FAILED = 3

        CHOICES = [
            (UNDEFINED, 'Undefined'),
            (PENDING, 'Pending'),
            (SUCCESS, 'Success'),
            (FAILED, 'Failed'),
        ]

        _default_value, _name = CHOICES[0]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    user = models.ForeignKey(User, models.PROTECT)
    program = models.ForeignKey('Program', models.PROTECT)
    currency = models.ForeignKey('exchange.Currency', models.PROTECT, related_name='+')
    amount = fields.FixedDecimalField(validators=[validators.MinValueValidator(limit_value=0)])
    wallet = models.ForeignKey('Wallet', models.PROTECT, help_text="Link to wallet with user wallet for Reward currency")
    account = models.ForeignKey('Account', models.PROTECT, help_text="Program Account with all Rewards")
    status = models.IntegerField(choices=Status.CHOICES, default=Status.UNDEFINED)
    created_at = models.DateTimeField(auto_now=True)

    def create_claim_reward(self):
        with transaction.atomic():
            # Account.objects.filter(id=self.account_id).update(balance=F("balance") - self.amount)
            Wallet.objects.filter(id=self.wallet_id).update(balance=F("balance") - self.amount)

        TreasuryAPI().treasury_wallet_controller().transfer_to_main(self.account.treasury_id, self.wallet.get_wallet(self.currency.code).id, str(self.amount))

        self.status = ClaimReward.Status.SUCCESS
        self.save()

    class Meta:
        ordering = ['-created_at', 'id']
        constraints = [
            models.CheckConstraint(check=models.Q(amount__gte=0), name='amount_gte_0')
        ]

    def __str__(self):
        return f'Claim reward #{self.id}.'
