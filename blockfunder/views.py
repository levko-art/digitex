import django_filters
from django.utils import timezone
from rest_framework import generics, permissions

from blockfunder.pagintations import *
from blockfunder.serializers import *
from blockfunder.models import *

__all__ = 'ListOfPrograms',  'GetProgramById', 'ListCreateTransaction', 'ListAllTransactionByProgram', 'AgreementView', 'ListAllTransaction', 'ListTransaction',

from common.permissions import KycPassedPermission


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


class ListOfPrograms(generics.ListAPIView):
    """
    Info about all BlockFunder programs
    program/
    """

    serializer_class = ProgramSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Program.objects.prefetch_related('deposit_currency', 'reward_currency')

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request and self.request.user.is_staff:
            return queryset.filter(is_enable=True)
        else:
            return queryset.filter(is_enable=True, is_visible=True)


class GetProgramById(generics.RetrieveAPIView):
    """
    Info about program by UUID
    program/<uuid:program_id>/
    """

    serializer_class = ProgramSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Program.objects.prefetch_related('deposit_currency', 'reward_currency')
    lookup_url_kwarg = 'program_id'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request and self.request.user.is_staff:
            return queryset.filter(is_enable=True)
        else:
            return queryset.filter(is_enable=True, is_visible=True)


class ListCreateTransaction(generics.ListCreateAPIView):
    """
    program/<uuid:program_id>/transaction/
    """

    queryset = Transaction.objects
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TransactionPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = TransactionFilter

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user, program=self.kwargs['program_id'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['program_id'] = self.kwargs['program_id']
        return context

    def perform_create(self, serializer):
        program = serializer.validated_data["program"]
        if not program.buy_enable:
            self.permission_denied(self.request, message="Transaction: Buy not enabled", code="-10000")
        if program.begin_date > timezone.now():
            self.permission_denied(self.request, message="Transaction: Program not started", code="-10000")
        if program.end_date < timezone.now():
            self.permission_denied(self.request, message="Transaction: Program ended", code="-10000")
        return super().perform_create(serializer)


class AgreementView(generics.RetrieveUpdateAPIView):
    queryset = LicenseAgreement.objects
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = LicenseAgreementSerializer


class ListAllTransactionByProgram(generics.ListAPIView):
    """
    program/<uuid:program_id>/all_transaction/
    """

    queryset = Transaction.objects.prefetch_related('deposit_currency', 'program', 'program__reward_currency').filter(status=Transaction.Status.SUCCESS)
    serializer_class = TransactionSerializer
    permission_classes = []
    pagination_class = TransactionPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = TransactionFilter

    def get_queryset(self):
        return super().get_queryset().filter(program=self.kwargs['program_id'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['program_id'] = self.kwargs['program_id']
        return context


class ListAllTransaction(generics.ListAPIView):
    """
    TODO: add filtration
    program/<uuid:program_id>/all_transaction/
    """

    queryset = Transaction.objects.prefetch_related('deposit_currency', 'program', 'program__reward_currency').filter(status=Transaction.Status.SUCCESS)
    serializer_class = TransactionSerializer
    permission_classes = []
    pagination_class = TransactionPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = TransactionFilter

    def get_queryset(self):
        return super().get_queryset()


class ListTransaction(generics.ListAPIView):
    """
    TODO: add filtration
    program/<uuid:program_id>/all_transaction/
    """

    queryset = Transaction.objects.prefetch_related('deposit_currency', 'program', 'program__reward_currency')
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TransactionPagination
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = TransactionFilter

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
