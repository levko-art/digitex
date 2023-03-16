from django.db.models.signals import post_save
from django.apps import AppConfig


class BlockfunderConfig(AppConfig):
    name = 'blockfunder'
    verbose_name = "Blockfunder"

    def ready(self):
        import blockfunder.signals
        from blockfunder.models import Transaction
        from blockfunder.models import Program

        post_save.connect(blockfunder.signals.push_transaction, sender=Transaction, dispatch_uid='push_transaction')
        post_save.connect(blockfunder.signals.create_program_accounts, sender=Program, dispatch_uid='create_program_accounts')
