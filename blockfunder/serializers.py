from django.contrib.auth.models import User
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce

from common.errors import unexpected_error
from common.templatetags import mask_email
from exchange.serializers import CurrencySerializer, SignedRateSerializer
from common.fields import FixedDecimalField
from common.helpers import get_client_ip
from rest_framework import serializers
from exchange.models import Currency
from django.conf import settings
from blockfunder.models import *
import decimal

__all__ = 'ProgramSerializer', 'TransactionSerializer', 'LicenseAgreementSerializer',


class LicenseAgreementSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    text = serializers.CharField(read_only=True)
    link = serializers.CharField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    confirmed = serializers.SerializerMethodField()

    def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')

    def update(self, instance, validated_data):
        obj, created = LicenseAgreementConfirmation.objects.get_or_create(user=validated_data['user'], license=instance)
        if created:
            obj.ip = get_client_ip(self.context['request'], settings.PROXY_TRUSTED_IPS)
            obj.user_agent = self.context['request'].META['HTTP_USER_AGENT'][:200]
            obj.save()
        return instance

    def get_confirmed(self, instance):
        user: User
        user = self.context['request'].user
        return user.is_authenticated and LicenseAgreementConfirmation.objects.filter(user=user, license=instance).exists()


class ProgramLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramLink
        fields = ['name', 'hyperlink']


class UserSaleStats(serializers.Serializer):
    total_txs = FixedDecimalField(min_value=0, read_only=True)
    total_amount_usd = FixedDecimalField(min_value=0, read_only=True)
    total_amount2 = FixedDecimalField(min_value=0, read_only=True)
    total_amount2_usd = FixedDecimalField(min_value=0, read_only=True)

    def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def __str__(self):
        return 'Serializer for UserSaleStats model.'


class ProgramSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.SlugField()
    begin_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    deposit_currency = CurrencySerializer(many=True)
    reward_currency = CurrencySerializer()
    hard_cap = FixedDecimalField()
    rate = FixedDecimalField()
    reward_total = FixedDecimalField()
    reward_remaining = FixedDecimalField()
    is_enable = serializers.BooleanField()
    is_visible = serializers.BooleanField()
    description = serializers.CharField()
    phase = serializers.IntegerField()
    phase_description = serializers.CharField()
    phase_info = serializers.CharField()
    links = ProgramLinkSerializer(many=True)
    participants = serializers.IntegerField()
    agreement = LicenseAgreementSerializer(many=True)
    affiliate = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    finish_type = serializers.CharField(read_only=True)
    lock_type = serializers.CharField(read_only=True)
    buy_enable = serializers.BooleanField()
    user_sale_stats = serializers.SerializerMethodField()

    class Meta:
        model = Program
        fields = ['id', 'name', 'slug', 'begin_date', 'end_date', 'deposit_currency', 'reward_currency', 'hard_cap', 'is_enable', 'is_visible', 'description', 'phase', 'phase_description', 'phase_info', 'links', 'agreement', 'affiliate', 'finish_type', 'lock_type', 'buy_enable', 'affiliate_rate', 'user_sale_stats', 'reward_remaining', 'participants', 'rate', 'reward_total']

    def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def __str__(self):
        return 'Serializer for Program model.'

    def get_user_sale_stats(self, instance: Program):
        user: User
        user = self.context['request'].user
        if user.is_authenticated:
            total_amount_usd = decimal.Decimal(0)
            for transaction in instance.transaction_set.filter(user=self.context['request'].user).values('deposit_currency').annotate(amount=Sum('amount')).order_by():
                total_amount_usd += transaction['amount'] * Currency.objects.get(pk=transaction['deposit_currency']).usd_rate
            total_amount2 = instance.transaction_set.filter(user=self.context['request'].user).aggregate(
                amount=Coalesce(Sum('amount2'), 0, output_field=DecimalField()))['amount']
            total_amount2_usd = total_amount2 * instance.rate
            user_sale_stats = UserSaleStats(
                {
                    'total_txs': instance.transaction_set.filter(user=self.context['request'].user).count(),
                    'total_amount_usd': total_amount_usd,
                    'total_amount2': total_amount2,
                    'total_amount2_usd': total_amount2_usd
                }
            )
            return user_sale_stats.data
        else:
            return None


class TransactionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    email = serializers.SerializerMethodField()
    deposit_currency = CurrencySerializer(read_only=True)
    currency_code = serializers.SlugRelatedField(slug_field='code', queryset=Currency.objects.all(), write_only=True, help_text="Currency code of transaction. Must be the same as program transaction_currency", required=True)
    amount = FixedDecimalField(min_value=0, required=True)
    amount2 = FixedDecimalField(min_value=0, read_only=True)
    rate = FixedDecimalField(min_value=0, read_only=True)
    signed_rate = SignedRateSerializer(write_only=True, required=False)
    reward_currency = CurrencySerializer(read_only=True, source='program.reward_currency')
    created_at = serializers.DateTimeField(read_only=True)
    status = serializers.ChoiceField(choices=Transaction.Status.CHOICES, read_only=True)
    program = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'deposit_currency', 'currency_code', 'reward_currency', 'created_at', 'status', 'program', 'user', 'email', 'amount', 'amount2', 'rate', 'signed_rate']

    def get_email(self, obj):
        return mask_email(obj.user.email)

    def validate(self, attrs):
        attrs['program'] = Program.objects.get(is_enable=True, pk=self.context["program_id"])
        attrs['deposit_wallet'], created = Wallet.objects.get_or_create(user=self.context["request"].user, type=Wallet.Type.DEPOSIT, program=attrs['program'])
        attrs['reward_wallet'], created = Wallet.objects.get_or_create(user=self.context["request"].user, type=Wallet.Type.REWARD, program=attrs['program'])
        attrs['deposit_account'], created = Account.objects.get_or_create(type=Account.Type.DEPOSIT, program=attrs['program'], currency=attrs['currency_code'])
        attrs['reward_account'], created = Account.objects.get_or_create(type=Account.Type.REWARD, program=attrs['program'], currency=attrs['program'].reward_currency)
        attrs['deposit_currency'] = attrs['currency_code']
        del attrs['currency_code']

        if 'signed_rate' in attrs:
            if attrs['signed_rate']['currency_from'].code != attrs['deposit_currency'].code:
                raise serializers.ValidationError("Invalid rate", unexpected_error)
            if attrs['signed_rate']['currency_to'].code != 'USD':
                raise serializers.ValidationError("Invalid rate", unexpected_error)

            attrs['rate'] = attrs['signed_rate']['rate']
            del attrs['signed_rate']
        return attrs

    def create(self, validated_data):
        return Transaction.objects.create(**validated_data)

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def __str__(self):
        return 'Serializer for Transaction model.'
