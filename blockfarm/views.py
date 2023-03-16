import django_filters
from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions
from blockfarm.serializers import *
from blockfarm.models import *
from common.paginator import DRFCursorPagination

__all__ = 'ListCreateTransaction', 'ListTransaction', 'ListCreateClaimReward', 'ListClaimReward', 'ListOfPrograms', 'ListRewardsByProgram', 'ListRewards', 'GetProgramById', 'GetRewardStatusByUserAndProgram'


class TransactionPagination(DRFCursorPagination):
    page_size = 100
    max_page_size = 1000
    page_size_query_param = 'page_size'
    ordering = '-created_at'


class TransactionFilter(django_filters.FilterSet):
    created_at_to = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lt", label='created_at To')
    created_at_from = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte", label='created_at From')

    def __init__(self, data=None, *args, **kwargs):
        # if filterset is bound, use initial values as defaults
        if data is not None:
            # get a mutable copy of the QueryDict
            data = data.copy()

            for name, f in self.base_filters.items():
                initial = f.extra.get('initial')

                # filter param is either missing or empty, use initial as default
                if not data.get(name) and initial:
                    data[name] = initial

        super().__init__(data, *args, **kwargs)

    class Meta:
        model = Transaction
        fields = ['created_at_to', 'created_at_from', ]


class ListCreateTransaction(generics.ListCreateAPIView):
    """
    program/<int:program_id>/transaction/
    """

    queryset = Transaction.objects
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TransactionPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = TransactionFilter

    def get_queryset(self):
        return super().get_queryset().filter(wallet__user=self.request.user, program=self.kwargs['program_id'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['program_id'] = self.kwargs['program_id']
        return context

    def perform_create(self, serializer):
        return super().perform_create(serializer)


class ListTransaction(generics.ListAPIView):
    queryset = Transaction.objects
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TransactionPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = TransactionFilter

    def get_queryset(self):
        return super().get_queryset().filter(wallet__user=self.request.user, program__is_enable=True)


class ClaimRewardPagination(DRFCursorPagination):
    page_size = 100
    max_page_size = 1000
    page_size_query_param = 'page_size'
    ordering = '-created_at'


class ClaimRewardFilter(django_filters.FilterSet):
    created_at_to = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lt", label='created_at To')
    created_at_from = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte", label='created_at From')

    def __init__(self, data=None, *args, **kwargs):
        # if filterset is bound, use initial values as defaults
        if data is not None:
            # get a mutable copy of the QueryDict
            data = data.copy()

            for name, f in self.base_filters.items():
                initial = f.extra.get('initial')

                # filter param is either missing or empty, use initial as default
                if not data.get(name) and initial:
                    data[name] = initial

        super().__init__(data, *args, **kwargs)

    class Meta:
        model = ClaimReward
        fields = ['created_at_to', 'created_at_from', ]


class ListCreateClaimReward(generics.ListCreateAPIView):
    """
    program/<int:program_id>/claim_reward/
    """

    queryset = ClaimReward.objects
    serializer_class = ClaimRewardSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ClaimRewardPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = ClaimRewardFilter

    def get_queryset(self):
        return super().get_queryset().filter(wallet__user=self.request.user, program=self.kwargs['program_id'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['program_id'] = self.kwargs['program_id']
        return context

    def perform_create(self, serializer):
        program = serializer.validated_data["program"]
        if not program.claim_enabled:
            self.permission_denied(
                self.request,
                message="Claiming",
                code="-10000"
            )
        return super().perform_create(serializer)


class ListClaimReward(generics.ListCreateAPIView):
    """
    program/<int:program_id>/claim_reward/
    """

    queryset = ClaimReward.objects
    serializer_class = ClaimRewardSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ClaimRewardPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = ClaimRewardFilter

    def get_queryset(self):
        return super().get_queryset().filter(wallet__user=self.request.user)


class ListOfPrograms(generics.ListAPIView):
    """
    Info about all BlockFarm programs
    program/
    """

    serializer_class = ProgramSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Program.objects.select_related('transaction_currency', 'reward_currency')

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request and self.request.user.is_staff:
            return queryset.filter(is_enable=True)
        else:
            return queryset.filter(is_enable=True, is_visible=True)


class RewardPagination(DRFCursorPagination):
    page_size = 100
    max_page_size = 1000
    page_size_query_param = 'page_size'
    ordering = '-created_at'


class RewardFilter(django_filters.FilterSet):
    created_at_to = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lt", label='created_at To')
    created_at_from = django_filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte", label='created_at From')

    def __init__(self, data=None, *args, **kwargs):
        # if filterset is bound, use initial values as defaults
        if data is not None:
            # get a mutable copy of the QueryDict
            data = data.copy()

            for name, f in self.base_filters.items():
                initial = f.extra.get('initial')

                # filter param is either missing or empty, use initial as default
                if not data.get(name) and initial:
                    data[name] = initial

        super().__init__(data, *args, **kwargs)

    class Meta:
        model = Reward
        fields = ['created_at_to', 'created_at_from', ]


class ListRewardsByProgram(generics.ListAPIView):
    """
    program/<int:program_id>/reward/
    """

    serializer_class = RewardSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Reward.objects
    pagination_class = RewardPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = RewardFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user, program=self.kwargs['program_id'])


class ListRewards(generics.ListAPIView):
    """
    program/<int:program_id>/reward/
    """

    serializer_class = RewardSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Reward.objects
    pagination_class = RewardPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = RewardFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.request.user)


class GetProgramById(generics.RetrieveAPIView):
    """
    Info about program by UUID
    program/<uuid:program_id>/
    """

    serializer_class = ProgramSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Program.objects.select_related('transaction_currency', 'reward_currency')
    lookup_url_kwarg = 'program_id'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request and self.request.user.is_staff:
            return queryset.filter(is_enable=True)
        else:
            return queryset.filter(is_enable=True, is_visible=True)


class GetRewardStatusByUserAndProgram(generics.RetrieveAPIView):
    """
    program/<int:program_id>/reward_status/
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = Program.objects
    lookup_url_kwarg = 'program_id'
    serializer_class = RewardStatusSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request and self.request.user.is_staff:
            return queryset.filter(is_enable=True)
        else:
            return queryset.filter(is_enable=True, is_visible=True)

    def get_object(self):
        program = super().get_object()

        stack_wallet, created = Wallet.objects.get_or_create(user=self.request.user, type=Wallet.Type.DEPOSIT,
                                                             program=program)
        reward_wallet, created = Wallet.objects.get_or_create(user=self.request.user, type=Wallet.Type.REWARD,
                                                              program=program)
        total_claimed = ClaimReward.objects.filter(user=self.request.user, program=program,
                                                   status=ClaimReward.Status.SUCCESS).aggregate(
            amount=Coalesce(Sum('amount'), 0, output_field=DecimalField()))['amount']

        return {
            'current_stacked': stack_wallet.balance,
            'current_rewarded': reward_wallet.balance,
            'total_claimed': total_claimed,
        }
