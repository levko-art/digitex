from django.core.management import BaseCommand

from blockfarm.tasks import check_deposit_balance


class Command(BaseCommand):
    help = 'Force create rewards'

    def handle(self, *args, **options):
        check_deposit_balance()
