import json
import os
from datetime import datetime
from typing import List

from django.db import IntegrityError, transaction

from citizens.models import Company, Citizen, EyeColor, Address, Food, Tag

CURRENT_DIR = os.path.dirname(__file__)
PEOPLE_RESOURCE_FILENAME = os.path.join(CURRENT_DIR, 'json', 'people.json')
COMPANIES_RESOURCE_FILENAME = os.path.join(CURRENT_DIR, 'json',
                                           'companies.json')

# See: https://en.wikipedia.org/wiki/ISO/IEC_5218
GENDER_TO_GENDER_CODE = {'male': 1, 'female': 2}

EXPECTED_FIELDS_PEOPLE = {
    '_id', 'index', 'guid', 'has_died', 'balance', 'picture', 'age',
    'eyeColor', 'name', 'gender', 'company_id', 'email', 'phone', 'address',
    'about', 'registered', 'tags', 'friends', 'greeting', 'favouriteFood'
}


class DataImportError(Exception):
    pass


def get_data_from_json_file(filename):
    with open(filename, mode='r') as file:
        json_data = json.load(file)
    return json_data


@transaction.atomic()
def import_companies(json_data):
    companies_to_create = []
    for entry in json_data:
        try:
            index = entry['index']
            name = entry['company']
        except KeyError:
            raise DataImportError(f'Found malformed company entry:\n{entry}')


        new_company = Company(id=index, name=name)
        companies_to_create.append(new_company)

    Company.objects.bulk_create(companies_to_create)


@transaction.atomic
def import_people(json_data):
    friends_relations = {}

    citizens_to_create = []
    for entry in json_data:
        if set(entry.keys()) != EXPECTED_FIELDS_PEOPLE:
            raise DataImportError(f'Found malformed citizen entry:\n{entry}')

        friends_relations[entry['index']] = [
            friend['index'] for friend in entry['friends']
        ]

        balance_in_cents = _raw_balance_to_cents(entry['balance'])
        favourite_food = _create_food_data(entry['favouriteFood'])
        tags = _create_tags(entry['tags'])
        registered_at = datetime.fromisoformat(entry['registered'])
        eye_color, _ = EyeColor.objects.get_or_create(
            color_name=entry['eyeColor']
        )
        address = _create_address(entry['address'])
        citizen = Citizen(
            _id=entry['_id'],
            id=entry['index'],
            guid=entry['guid'],
            has_died=entry['has_died'],
            picture_url=entry['picture'],
            age=entry['age'],
            name=entry['name'],
            email=entry['email'],
            about=entry['about'],
            greeting=entry['greeting'],
            gender_code=GENDER_TO_GENDER_CODE.get(entry['gender'], 0),
            registered_at=registered_at,
            balance_in_cents=balance_in_cents,
            eye_color=eye_color,
            phone_number=entry['phone'],
            address=address,
            company_id=_company_id_to_index(entry['company_id'])
        )
        citizen.favourite_food.set(favourite_food)
        citizen.tags.set(tags)
        citizens_to_create.append(citizen)

    created_citizens = Citizen.objects.bulk_create(citizens_to_create)

    # This implementation makes this function grow to O(2n) in complexity
    # but ensures data integrity.
    for citizen in created_citizens:
        citizen.friends.set(friends_relations[citizen.id])


def _create_food_data(raw_favourite_food_list: List[str]) -> List[Food]:
    favourite_food = []
    for food in raw_favourite_food_list:
        if food in Food.KNOWN_FRUITS:
            _type = Food.FRUIT
        elif food in Food.KNOWN_VEGETABLES:
            _type = Food.VEGETABLE
        else:
            _type = Food.OTHER
        new_food = Food(name=food, type=_type)
        favourite_food.append(new_food)

    Food.objects.bulk_create(favourite_food, ignore_conflicts=True)
    # Ignoring conflicts on bulk creation causes the returned objects to not
    # have ids so we have to refetch them. This causes a read on every citizen
    # but it's better than multiple tag writes per citizen.
    return Food.objects.filter(name__in=raw_favourite_food_list)


def _create_tags(raw_tags_list: List[str]) -> List[Tag]:
    tags = [Tag(name=tag) for tag in raw_tags_list]
    Tag.objects.bulk_create(tags, ignore_conflicts=True)
    # Ignoring conflicts on bulk creation causes the returned objects to not
    # have ids so we have to refetch them. This causes a read on every citizen
    # but it's better than multiple tag writes per citizen.
    return Tag.objects.filter(name__in=raw_tags_list)


def _create_address(raw_address_entry: str) -> Address:
    (
        street_address,
        city_name,
        state_name,
        post_code
    ) = raw_address_entry.split(',')
    return Address.objects.create(
        street_address=street_address.strip(),
        city_name=city_name.strip(),
        state_name=state_name.strip(),
        post_code=post_code.strip(),
    )


def _raw_balance_to_cents(raw_balance: str) -> int:
    """
    Format a raw balance string into a number of cents.

    NOTE:
    Supports one format of balance only: $2,418.59
    Needs refactoring if we ever need to support different balance string types
    """
    dollars, cents = raw_balance.replace('$', '').replace(',', '').split('.')
    return int(dollars) * 100 + int(cents)


def _company_id_to_index(company_id: int) -> int:
    """
    This is a very odd function that seem to make little sense. It exists since
    after inspecting the provided resource files it looks like there's a
    mismatch between the company_ids provided and the index values of the
    companies themselves.

    It looks like a safe guess that they are offset by one (the indexes go from
    0 to 99 and the ids go from 1 to 100) but in a real life scenario this
    would need confirmation and documentation.
    """
    return company_id - 1
