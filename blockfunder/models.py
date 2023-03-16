import decimal
import logging

from digitex_engine_treasury_client import ApiException
from django.contrib.auth.models import User
from django.core import validators
from django.db.models import F
from common.helpers import TreasuryAPI
from django.db import models, transaction
from exchange import fields
import uuid
from exchange.models import MainTrader
from affiliate.models import Payout, Profile

__all__ = 'Program', 'ProgramLink', 'Account', 'Wallet', 'Transaction', 'LicenseAgreement', 'LicenseAgreementConfirmation',

logger = logging.getLogger(__name__)


class Program(models.Model):

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=128, default='')
    slug = models.SlugField(max_length=64, null=False, blank=False)
    begin_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    deposit_currency = models.ManyToManyField('exchange.Currency', blank=False)
    reward_currency = models.ForeignKey('exchange.Currency', on_delete=models.PROTECT, related_name='+')
    hard_cap = fields.FixedDecimalField(default=0.0)
    rate = fields.FixedDecimalField(default=0.0)
    is_enable = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=False)
    description = models.CharField(max_length=2048, blank=True)
    phase = models.IntegerField(default=1)
    phase_description = models.CharField(max_length=2048, blank=True)
    phase_info = models.TextField(blank=True)
    links = models.ManyToManyField('ProgramLink', blank=True)
    agreement = models.ManyToManyField('LicenseAgreement', blank=True)
    affiliate = models.ForeignKey('affiliate.Program', on_delete=models.SET_NULL, null=True)
    finish_type = models.CharField(max_length=128, null=True, blank=True)
    lock_type = models.CharField(max_length=256, null=True, blank=True)
    buy_enable = models.BooleanField(default=True)
    affiliate_rate = fields.FixedDecimalField(default=0.0)

    def create_account(self):
        for currency in self.deposit_currency.all():
            Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=self, currency=currency)
        Account.objects.get_or_create(type=Account.Type.REWARD, program=self, currency=self.reward_currency)

    @property
    def participants(self) -> int:
        # TODO
        return 0

    @property
    def reward_total(self) -> decimal.Decimal:
        return self.account_set.get(type=Account.Type.REWARD).total

    @property
    def reward_remaining(self) -> decimal.Decimal:
        return self.account_set.get(type=Account.Type.REWARD).balance

    def __str__(self):
        return f'Program #{self.id}.'


class ProgramLink(models.Model):
    name = models.CharField(max_length=128)
    hyperlink = models.CharField(max_length=512)


class Account(models.Model):

    class Type:
        DEPOSIT = 0
        REWARD = 1

        CHOICES = [
            (DEPOSIT, 'Deposit account'),
            (REWARD, 'Reward account'),
        ]

        _default_value, _name = CHOICES[0]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    type = models.IntegerField(choices=Type.CHOICES)
    currency = models.ForeignKey('exchange.Currency', models.PROTECT, related_name='+')
    balance = fields.FixedDecimalField(default=0.0, validators=[validators.MinValueValidator(limit_value=0)])
    total = fields.FixedDecimalField(default=decimal.Decimal("0"))
    treasury_id = models.IntegerField(null=True)
    program = models.ForeignKey('Program', models.PROTECT, null=False, blank=False)

    def __str__(self):
        return f'{self.type} account #{self.id}.'


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
    user = models.ForeignKey(User, models.PROTECT, null=False, blank=False, related_name='+')
    balance = fields.FixedDecimalField(default=0, validators=[validators.MinValueValidator(limit_value=0)])
    program = models.ForeignKey('Program', models.PROTECT, null=False, blank=False)
    total_rewarded = fields.FixedDecimalField(default=0, validators=[validators.MinValueValidator(limit_value=0)])

    def get_wallet(self, currency_code):
        trader = MainTrader.objects.get(user=self.user)
        return trader.get_wallet(currency_code)

    def __str__(self):
        return f'Wallet #{self.id}, User: {self.user}.'


class Transaction(models.Model):

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
    user = models.ForeignKey(User, models.PROTECT, related_name='+')
    deposit_currency = models.ForeignKey('exchange.Currency', models.PROTECT, related_name='+')
    amount = fields.FixedDecimalField(validators=[validators.MinValueValidator(limit_value=0)])
    amount2 = fields.FixedDecimalField(validators=[validators.MinValueValidator(limit_value=0)], null=True)
    rate = fields.FixedDecimalField(null=True)
    deposit_wallet = models.ForeignKey('Wallet', models.PROTECT, related_name='TRANSACTION_deposit_wallet')
    deposit_account = models.ForeignKey('Account', models.PROTECT, related_name='TRANSACTION_deposit_account')
    reward_wallet = models.ForeignKey('Wallet', models.PROTECT, related_name='TRANSACTION_reward_wallet')
    reward_account = models.ForeignKey('Account', models.PROTECT, related_name='TRANSACTION_reward_account')
    created_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(choices=Status.CHOICES, default=Status.UNDEFINED)
    program = models.ForeignKey('Program', models.PROTECT, null=False, blank=False)
    rewarded = models.BooleanField(default=False)
    buy_out = models.BooleanField(default=False)

    def create_transaction(self):
        if self.rate:
            rate = self.rate
        else:
            rate = self.deposit_currency.usd_rate

        Wallet.objects.select_for_update().filter(id=self.reward_wallet.id)
        if self.reward_wallet.total_rewarded + (self.amount * rate / self.program.rate) <= self.program.hard_cap:

            def create_affiliate_payout(tx: Transaction):
                try:
                    affiliate_parent = Profile.objects.get(user=tx.user, program=tx.program.affiliate).parent
                    if affiliate_parent:
                        Payout.objects.create(user=affiliate_parent.user, program=tx.program.affiliate,
                                              reason=f'blockfunder transaction #{tx.id}',
                                              currency=tx.deposit_currency,
                                              wallet_id=tx.deposit_account.treasury_id,
                                              amount=tx.amount * tx.program.affiliate_rate)
                except Profile.DoesNotExist:
                    logging.exception("Blockfunder: Affiliate profile not exists")
                    pass

            try:
                amount_to_reward = self.amount * rate / self.program.rate

                kwargs = {
                    "amount1": str(self.amount),
                    "amount2": str(amount_to_reward)
                }

                if self.buy_out:
                    kwargs["buyout"] = True

                response = TreasuryAPI().treasury_wallet_controller().swap(self.deposit_wallet.get_wallet(self.deposit_currency.code).id,
                                                                           self.reward_account.treasury_id,
                                                                           self.reward_wallet.get_wallet(self.program.reward_currency.code).id,
                                                                           self.deposit_account.treasury_id,
                                                                           **kwargs
                                                                           )
                with transaction.atomic():
                    Account.objects.filter(id=self.deposit_account_id).update(balance=F("balance") + response.amount1)
                    Wallet.objects.filter(id=self.deposit_wallet_id).update(balance=F("balance") - response.amount1)
                    Account.objects.filter(id=self.reward_account_id).update(balance=F("balance") - response.amount2)
                    Wallet.objects.filter(id=self.reward_wallet_id).update(balance=F("balance") + response.amount2, total_rewarded=F("total_rewarded") + response.amount2)
                    self.amount1 = response.amount1
                    self.amount2 = response.amount2
                    self.status = Transaction.Status.SUCCESS
                    self.save()

                try:
                    if self.program.affiliate:
                        create_affiliate_payout(self)
                except:
                    logger.exception("Blockfunder: create_affiliate_payout exception")
                    pass

            except ApiException as ex:
                logger.exception("Blockfunder: APIException")
                self.status = Transaction.Status.FAILED
                self.save()
            except Exception as ex:
                logger.exception("Blockfunder: Exception")
                self.status = Transaction.Status.FAILED
                self.save()
        else:
            logger.exception("Blockfunder: Above hardcap")
            self.status = Transaction.Status.FAILED
            self.save()

    def __str__(self):
        return f'Transaction #{self.id}.'


class LicenseAgreement(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=512)
    text = models.TextField(blank=True)
    link = models.URLField(blank=True)

    def __str__(self):
        return f'Licence agreement #{self.id}.'


class LicenseAgreementConfirmation(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    user = models.ForeignKey(User, models.PROTECT, related_name='+')
    license = models.ForeignKey('LicenseAgreement', on_delete=models.CASCADE)
    ip = models.GenericIPAddressField(blank=True, null=True, unpack_ipv4=True)
    user_agent = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'license'], name='unique_user_license')
        ]

    def __str__(self):
        return f'Licence agreement confirmation #{self.id}.'
