from django.urls import path

from blockfarm.views import *

urlpatterns = [
    path('program/', ListOfPrograms.as_view(), name='all-programs'),
    path('program/<uuid:program_id>/', GetProgramById.as_view(), name='program-by-trader'),
    path('program/<uuid:program_id>/reward/', ListRewardsByProgram.as_view(), name='reward-by-program'),
    path('program/<uuid:program_id>/transaction/', ListCreateTransaction.as_view(), name='create-transaction'),
    path('program/<uuid:program_id>/claim_reward/', ListCreateClaimReward.as_view(), name='create-claim-reward'),
    path('program/<uuid:program_id>/reward_status/', GetRewardStatusByUserAndProgram.as_view(), name='reward-status-by-user-and-program'),
    path('reward/', ListRewards.as_view(), name='list-reward'),
    path('transaction/', ListTransaction.as_view(), name='list-transaction'),
    path('claim_reward/', ListClaimReward.as_view(), name='list-claim-reward'),

]

# urlpatterns = format_suffix_patterns(urlpatterns)
