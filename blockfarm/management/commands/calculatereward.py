from django.core.management import BaseCommand

from blockfarm.tasks import calculating_rewards


class Command(BaseCommand):
    help = 'Force create rewards'

    # def add_arguments(self, parser):
    #     parser.add_argument('program_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        calculating_rewards()
