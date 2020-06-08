from django.core.management import BaseCommand
from django.db import transaction

from citizens.resources.importers import import_companies, import_people, \
    get_data_from_json_file, COMPANIES_RESOURCE_FILENAME, \
    PEOPLE_RESOURCE_FILENAME


class Command(BaseCommand):
    help = "Import people.json and companies.json resources"

    @transaction.atomic
    def handle(self, **options):
        companies_data = get_data_from_json_file(COMPANIES_RESOURCE_FILENAME)
        import_companies(companies_data)

        people_data = get_data_from_json_file(PEOPLE_RESOURCE_FILENAME)
        import_people(people_data)
