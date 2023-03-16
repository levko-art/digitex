from django.apps import AppConfig
from django.db.models.signals import post_save


class BlockfarmConfig(AppConfig):
    name = 'blockfarm'
    verbose_name = "Blockfarm"

    def ready(self):
        import blockfarm.signals
        from blockfarm.models import Transaction
        from blockfarm.models import ClaimReward
        from blockfarm.models import Program
        from blockfarm.models import Reward

        post_save.connect(blockfarm.signals.push_transaction, sender=Transaction, dispatch_uid='push_transaction')
        post_save.connect(blockfarm.signals.push_claim_reward, sender=ClaimReward, dispatch_uid='push_claim_reward')
        post_save.connect(blockfarm.signals.create_program_accounts, sender=Program, dispatch_uid='create_program_accounts')
        post_save.connect(blockfarm.signals.push_reward, sender=Reward, dispatch_uid='push_reward')
