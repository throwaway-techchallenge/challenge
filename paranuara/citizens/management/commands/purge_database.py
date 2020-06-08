from django.core.management import BaseCommand
from django.db import transaction

from citizens.models import Citizen, EyeColor, Food, Tag, Company, Address


class Command(BaseCommand):
    help = "Remove all data from the database. " \
           "Useful if you want to import the same file multiple times."

    @transaction.atomic
    def handle(self, **options):
        Citizen.objects.all().delete()
        EyeColor.objects.all().delete()
        Food.objects.all().delete()
        Tag.objects.all().delete()
        Company.objects.all().delete()
        Address.objects.all().delete()
