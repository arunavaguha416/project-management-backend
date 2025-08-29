from django.core.management.base import BaseCommand
from django.db import transaction
from .seed_all import Command as SeedCommand

class Command(BaseCommand):
    help = 'Clear all data from the database'

    def handle(self, *args, **options):
        seeder = SeedCommand()
        seeder.clear_data()
        self.stdout.write(self.style.SUCCESS('Database cleared successfully!'))
