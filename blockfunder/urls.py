from django.urls import path

from blockfunder.views import *

urlpatterns = [
    path('program/', ListOfPrograms.as_view(), name='all-programs'),
    path('program/<uuid:program_id>/', GetProgramById.as_view(), name='program-by-uuid'),
    path('program/<uuid:program_id>/transaction/', ListCreateTransaction.as_view(), name='list-create-transaction'),
    path('agreement/<uuid:pk>/', AgreementView.as_view(), name='agreement'),
    path('program/<uuid:program_id>/all_transaction/', ListAllTransactionByProgram.as_view(), name='list-all-transaction-by-program'),
    path('all_transaction/', ListAllTransaction.as_view(), name='list-all-transaction'),
    path('transaction/', ListTransaction.as_view(), name='list-transaction'),
]
