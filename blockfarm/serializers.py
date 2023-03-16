from rest_framework import serializers

from blockfarm.fields import FixedDecimalField
from blockfarm.models import *
from common.utils.functional import round_down
from exchange.models import Currency

__all__ = 'ProgramLinkSerializer', 'ProgramSerializer', 'AccountSerializer', 'WalletSerializer', 'TransactionSerializer', 'RewardSerializer', 'ClaimRewardSerializer', 'RewardStatusSerializer',

from exchange.serializers import CurrencySerializer


class ProgramLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramLink
        fields = ['name', 'hyperlink']


class ProgramSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    transaction_currency = CurrencySerializer(read_only=True)
    reward_currency = CurrencySerializer(read_only=True)
    emit_duration = serializers.DurationField(read_only=True)
    begin_date = serializers.DateTimeField(read_only=True)
    end_date = serializers.DateTimeField(read_only=True)
    prestake_date = serializers.DateTimeField(read_only=True)
    total_staked = FixedDecimalField(read_only=True)
    total_rewards = FixedDecimalField(read_only=True)
    links = ProgramLinkSerializer(many=True, read_only=True)
    participants = serializers.IntegerField(read_only=True)
    apy = serializers.DecimalField(decimal_places=2, max_digits=18, read_only=True)
    max_participants = serializers.IntegerField(read_only=True)
    max_staked = FixedDecimalField(read_only=True)
    max_apy = serializers.DecimalField(decimal_places=2, max_digits=18, read_only=True)

    def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def __str__(self):
        return 'Serializer for Program model.'


class AccountSerializer(serializers.Serializer):

    types = ((0, 'Deposit account'), (1, 'Reward account'))

    type = serializers.ChoiceField(choices=types)
    program = ProgramSerializer()
    currency = serializers.SlugRelatedField(slug_field='code', read_only=True)
    balance = FixedDecimalField()
    treasury_id = serializers.IntegerField()

    def create(self, validated_data):
        return Account.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.type = validated_data.get('type', instance.type)
        instance.program = validated_data.get('program', instance.program)
        instance.currency = validated_data.get('currency', instance.currency)
        instance.balance = validated_data.get('balance', instance.balance)
        instance.treasury_id = validated_data.get('treasury_id', instance.treasury_id)

    def __str__(self):
        return 'Serializer for Account model.'


class WalletSerializer(serializers.Serializer):

    types = ((0, 'Deposit wallet'), (1, 'Reward wallet'))

    type = serializers.ChoiceField(choices=types)

    def create(self, validated_data):
        return Wallet.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.type = validated_data.get('type', instance.type)
        instance.user = validated_data.get('user', instance.user)

    def __str__(self):
        return 'Serializer for Wallet model.'


class TransactionSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    currency = CurrencySerializer(read_only=True)
    currency_code = serializers.SlugRelatedField(slug_field='code', queryset=Currency.objects.all(), write_only=True, help_text="Currency code of transaction. Must be the same as program transaction_currency", required=True)
    amount = FixedDecimalField(min_value=0, required=True)
    type = serializers.ChoiceField(choices=Transaction.Type.CHOICES, required=True)
    program = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    status = serializers.ChoiceField(choices=Transaction.Status.CHOICES, read_only=True)

    def validate(self, attrs):
        attrs['program'] = Program.objects.get(is_enable=True, pk=self.context["program_id"])
        attrs['wallet'], created = Wallet.objects.get_or_create(user=self.context["request"].user, type=Wallet.Type.DEPOSIT, program=attrs['program'])
        attrs['account'] = Account.objects.get(program=attrs['program'], type=Account.Type.DEPOSIT)
        attrs['currency'] = attrs['currency_code']
        del attrs['currency_code']
        attrs['amount'] = round_down(attrs['amount'], attrs['program'].transaction_currency.treasury_scale)
        return attrs

    def create(self, validated_data):
        return Transaction.objects.create(**validated_data)

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def __str__(self):
        return 'Serializer for Transaction model.'


class RewardSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    currency = CurrencySerializer(read_only=True)
    amount = FixedDecimalField(read_only=True)
    program = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    description = serializers.CharField(read_only=True)
    user_staked = FixedDecimalField(read_only=True)
    total_staked = FixedDecimalField(read_only=True)
    duration = serializers.DurationField(read_only=True)

    def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def __str__(self):
        return 'Serializer for Reward model.'


class ClaimRewardSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    currency = CurrencySerializer(read_only=True)
    amount = FixedDecimalField(min_value=0)
    program = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    status = serializers.ChoiceField(choices=ClaimReward.Status.CHOICES, read_only=True)

    def validate(self, attrs):
        attrs['program'] = Program.objects.get(is_enable=True, pk=self.context["program_id"])
        attrs['wallet'], created = Wallet.objects.get_or_create(user=self.context["request"].user,
                                                                type=Wallet.Type.REWARD, program=attrs['program'])
        attrs['account'] = Account.objects.get(program=attrs['program'], type=Account.Type.REWARD)
        attrs['currency'] = attrs['program'].reward_currency
        attrs['amount'] = round_down(attrs['amount'], attrs['program'].reward_currency.treasury_scale)
        return attrs

    def create(self, validated_data):
        return ClaimReward.objects.create(**validated_data)

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def __str__(self):
        return 'Serializer for ClaimReward model.'


class RewardStatusSerializer(serializers.Serializer):
    current_stacked = FixedDecimalField(read_only=True)
    current_rewarded = FixedDecimalField(read_only=True)
    total_claimed = FixedDecimalField(read_only=True)

    def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def __str__(self):
        return 'Serializer for RewardStatus.'
