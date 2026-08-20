from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction


class Command(BaseCommand):
    help = 'Safely purges existing demo records and creates a fresh set of realistic demo data.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=" * 70))
        self.stdout.write(self.style.NOTICE("   SAEC CAFE - RESETTING DEMO DATA (Purge + Seed)"))
        self.stdout.write(self.style.NOTICE("=" * 70))

        # Step 1: Remove existing demo data
        call_command('remove_demo_data')

        # Step 2: Seed fresh demo data
        call_command('seed_demo_data')

        self.stdout.write(self.style.SUCCESS("\n>> DEMO RESET COMPLETE: FRESH DEMO DATA READY (PASS) <<\n"))
