from datetime import datetime

import pytz
from django.test import TransactionTestCase

from citizens.models import Company, Citizen, Food, Tag
from citizens.resources.importers import import_companies, import_people, \
    DataImportError, _company_id_to_index


class CompaniesImporterTest(TransactionTestCase):

    def test_company_importer_happy_path(self):
        json_data = [
            {'index': 0, 'company': 'SOME_COMPANY'},
            {'index': 1, 'company': 'OTHER_COMPANY'}
        ]

        import_companies(json_data)

        created_companies = Company.objects.all().order_by('id')

        self.assertEqual(created_companies[0].name, 'SOME_COMPANY')
        self.assertEqual(created_companies[1].name, 'OTHER_COMPANY')
        self.assertEqual(len(created_companies), 2)

    def test_raises_error_on_malformed_company_data(self):
        json_data = [
            {'index': 0},
            {'index': 1, 'company': 'OTHER_COMPANY'}
        ]

        with self.assertRaises(DataImportError):
            import_companies(json_data)

        self.assertEqual(Company.objects.exists(), False)


class CitizenImporterTest(TransactionTestCase):
    TEST_CITIZEN_ENTRY = {
        "_id": "595eeb9b96d80a5bc7afb106",
        "index": 0,
        "guid": "5e71dc5d-61c0-4f3b-8b92-d77310c7fa43",
        "has_died": True,
        "balance": "$2,418.59",
        "picture": "http://placehold.it/32x32",
        "age": 61,
        "eyeColor": "blue",
        "name": "Carmella Lambert",
        "gender": "female",
        "company_id": 58,
        "email": "carmellalambert@earthmark.com",
        "phone": "+1 (910) 567-3630",
        "address": "628 Sumner Place, Sperryville, American Samoa, 9819",
        "about": "Non duis dolore ad enim.\r\n",
        "registered": "2016-07-13T12:29:07 -01:00",
        "tags": ["test_tag", "test_tag_two"],
        "friends": [],
        "greeting": "Hello!",
        "favouriteFood": [
            "beetroot",
            "strawberry",
            "mushroom",
        ]
    }
    SECOND_CITIZEN_ENTRY = TEST_CITIZEN_ENTRY.copy()
    SECOND_CITIZEN_ENTRY['index'] = 1
    SECOND_CITIZEN_ENTRY['_id'] = "595eeb9b96d80a5bc7afb106124"
    SECOND_CITIZEN_ENTRY['guid'] = "5e71dc5d-61c0-4f3b-8b92-1kljl23423"
    SECOND_CITIZEN_ENTRY['tags'] = ["test_tag"]
    SECOND_CITIZEN_ENTRY['friends'] = []

    MALFORMED_CITIZEN = {"index": 1}

    def setUp(self):
        # We need to create the company that TEST_CITIZEN_ENTRY refers to
        Company.objects.create(
            id=_company_id_to_index(58),
            name="SOME_COMPANY"
        )

    def test_basic_fields_import(self):
        json_data = [self.TEST_CITIZEN_ENTRY]

        import_people(json_data)

        all_citizens = Citizen.objects.all()
        citizen = all_citizens.first()
        source = json_data[0]
        self.assertEqual(len(all_citizens), 1)
        self.assertEqual(citizen._id, source['_id'])
        self.assertEqual(citizen.id, source['index'])
        self.assertEqual(citizen.guid, source['guid'])
        self.assertEqual(citizen.has_died, source['has_died'])
        self.assertEqual(citizen.picture_url, source['picture'])
        self.assertEqual(citizen.age, source['age'])
        self.assertEqual(citizen.name, source['name'])
        self.assertEqual(citizen.gender_code, 2)
        self.assertEqual(citizen.email, source['email'])
        self.assertEqual(citizen.about, source['about'])
        self.assertEqual(citizen.greeting, source['greeting'])
        self.assertEqual(citizen.registered_at,
                         datetime(year=2016, month=7, day=13,
                                  hour=13, minute=29, second=7,
                                  tzinfo=pytz.UTC
                                  )
                         )
        self.assertEqual(citizen.balance_in_cents, 241859)
        self.assertEqual(citizen.eye_color.color_name,
                         source['eyeColor'])
        self.assertEqual(citizen.phone_number, source['phone'])
        self.assertEqual(citizen.address.street_address, '628 Sumner Place')
        self.assertEqual(citizen.address.city_name, 'Sperryville')
        self.assertEqual(citizen.address.state_name, 'American Samoa')
        self.assertEqual(citizen.address.post_code, '9819')
        self.assertEqual(citizen.company.name, 'SOME_COMPANY')

    def test_raises_error_on_malformed_citizen_data(self):
        json_data = [self.MALFORMED_CITIZEN, self.TEST_CITIZEN_ENTRY]

        with self.assertRaises(DataImportError):
            import_people(json_data)

        self.assertEqual(Citizen.objects.exists(), False)

    def test_favourite_food_categorization(self):
        json_data = [self.TEST_CITIZEN_ENTRY]

        import_people(json_data)

        citizen = Citizen.objects.first()
        favourite_food_names = {f.name for f in citizen.favourite_food.all()}
        self.assertEqual(
            favourite_food_names,
            {
                'beetroot',
                'strawberry',
                'mushroom',
            }
        )

        vegetable = Food.objects.filter(type=Food.VEGETABLE).first()
        fruit = Food.objects.filter(type=Food.FRUIT).first()
        other = Food.objects.filter(type=Food.OTHER).first()
        self.assertEqual(vegetable.name, 'beetroot')
        self.assertEqual(fruit.name, 'strawberry')
        self.assertEqual(other.name, 'mushroom')
        self.assertEqual(len(Food.objects.all()), 3)

    def test_tags(self):
        json_data = [self.TEST_CITIZEN_ENTRY, self.SECOND_CITIZEN_ENTRY]

        import_people(json_data)

        all_tag_names = Tag.objects.all().values_list('name', flat=True)
        self.assertEqual(set(all_tag_names), {'test_tag', 'test_tag_two'})

    def test_friends(self):
        # Citizens being their own friends is assumed to be supported
        # since that happens in the provided initial resource files
        self.TEST_CITIZEN_ENTRY['friends'] = [{"index": 0}, {"index": 1}]

        # The relationship is asymmetric - this citizen does not consider
        # the original test citizen a friend.
        self.SECOND_CITIZEN_ENTRY['friends'] = []

        json_data = [self.TEST_CITIZEN_ENTRY, self.SECOND_CITIZEN_ENTRY]

        import_people(json_data)

        first_citizen = Citizen.objects.get(id=0)
        second_citizen = Citizen.objects.get(id=1)

        self.assertEqual(
            list(first_citizen.friends.all()),
            [first_citizen, second_citizen]
        )
        self.assertEqual(
            list(second_citizen.friends.all()),
            []
        )
