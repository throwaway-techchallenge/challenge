from collections import OrderedDict

from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APITestCase

from citizens.models import Citizen, Food, Address, EyeColor, Company
from citizens.rest.constants import INVALID_ID_FORMAT_ERROR_PAYLOAD, \
    NON_EXISTENT_RESOURCE_ERROR_PAYLOAD, NO_EMPLOYEES_ERROR_PAYLOAD


class SingleCitizenViewTest(APITestCase):
    TEST_CITIZEN_1_NAME = "Test Citizen 1"
    TEST_CITIZEN_1_AGE = 50

    def setUp(self):
        self.citizen = _create_test_citizen(
            name=self.TEST_CITIZEN_1_NAME,
            age=self.TEST_CITIZEN_1_AGE,
        )
        self.citizen.favourite_food.set(
            [
                Food.objects.create(name='carrot', type='vegetable'),
                Food.objects.create(name='apple', type='fruit'),
                Food.objects.create(name='mushroom', type='other')
            ]
        )

    def test_happy_path(self):
        url = _get_single_citizen_url(self.citizen.id)

        response = self.client.get(url)

        self.assertEqual(
            response.data,
            {
                "username": self.TEST_CITIZEN_1_NAME,
                "age": self.TEST_CITIZEN_1_AGE,
                "fruits": ['apple'],
                "vegetables": ['carrot'],
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_does_not_exist(self):
        non_existent_citizen_id = 42
        url = _get_single_citizen_url(non_existent_citizen_id)

        response = self.client.get(url)

        self.assertEqual(response.data, NON_EXISTENT_RESOURCE_ERROR_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_id_in_invalid_format(self):
        invalid_format_id = "this_is_totally_invalid"
        url = _get_single_citizen_url(invalid_format_id)

        response = self.client.get(url)

        self.assertEqual(response.data, INVALID_ID_FORMAT_ERROR_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_get_requests_allowed(self):
        url = _get_single_citizen_url(self.citizen.id)

        for http_method in [self.client.post, self.client.put, self.client.delete]:
            with self.subTest(http_method.__name__):
                response = self.client.post(url)

                self.assertEqual(response.status_code,
                                 status.HTTP_405_METHOD_NOT_ALLOWED)


class TwoCitizensViewTest(APITestCase):

    def setUp(self):
        blue = EyeColor.objects.create(color_name='blue')
        brown = EyeColor.objects.create(color_name='brown')

        self.TEST_CITIZEN_1_DATA = {
            'id': 1,
            'name': "Test Citizen 1",
            'age': 51,
            'address': Address.objects.create(
                street_address='1 One',
                city_name='One',
                state_name='One',
                post_code='1111'
            ),
            'phone_number': '+1 (111) 111 111'
        }
        self.TEST_CITIZEN_2_DATA = {
            'id': 2,
            'name': "Test Citizen 2",
            'age': 52,
            'address': Address.objects.create(
                street_address='2 Two',
                city_name='Two',
                state_name='Two',
                post_code='2222'
            ),
            'phone_number': ' "+1 (222) 222 222"'
        }
        self.OK_COMMON_FRIEND = {
            'id': 3,
            'name': "Test Citizen 3",
            'age': 53,
            'address': Address.objects.create(
                street_address='3 Two',
                city_name='Three',
                state_name='Three',
                post_code='333'
            ),
            'phone_number': '+1 (333) 333 333',
            'has_died': False,
            'eye_color': brown,
        }
        self.BLUE_EYED_COMMON_FRIEND = {
            'id': 4,
            'has_died': False,
            'eye_color': blue,
        }
        self.DEAD_COMMON_FRIEND = {
            'id': 5,
            'has_died': True,
            'eye_color': brown,
        }

        self.citizen_1 = _create_test_citizen(**self.TEST_CITIZEN_1_DATA)
        self.citizen_2 = _create_test_citizen(**self.TEST_CITIZEN_2_DATA)
        self.citizen_3 = _create_test_citizen(**self.OK_COMMON_FRIEND)
        self.citizen_4 = _create_test_citizen(**self.BLUE_EYED_COMMON_FRIEND)
        self.citizen_5 = _create_test_citizen(**self.DEAD_COMMON_FRIEND)

        self.citizen_1.friends.add(self.citizen_3)
        self.citizen_1.friends.add(self.citizen_4)
        self.citizen_1.friends.add(self.citizen_5)

        self.citizen_2.friends.add(self.citizen_3)
        self.citizen_2.friends.add(self.citizen_4)
        self.citizen_2.friends.add(self.citizen_5)

    def test_happy_path(self):
        url = _get_two_citizens_url(self.citizen_1.id, self.citizen_2.id)

        response = self.client.get(url)

        self.assertEqual(
            response.data,
            {
                'citizens': [
                    OrderedDict([
                        ('username', self.citizen_1.name),
                        ('age', self.citizen_1.age),
                        ('address', str(self.citizen_1.address)),
                        ('phone_number', self.citizen_1.phone_number)
                    ]),
                    OrderedDict([
                        ('username', self.citizen_2.name),
                        ('age', self.citizen_2.age),
                        ('address', str(self.citizen_2.address)),
                        ('phone_number', self.citizen_2.phone_number)
                    ])
                ],
                'common_live_brown_eyed_friends': [
                    OrderedDict([
                        ('username', self.citizen_3.name),
                        ('age', self.citizen_3.age),
                        ('address', str(self.citizen_3.address)),
                        ('phone_number', self.citizen_3.phone_number)
                    ])
                ]

            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_does_not_exist(self):
        non_existent_citizen_id = 42
        url = _get_two_citizens_url(self.citizen_1.id, non_existent_citizen_id)

        response = self.client.get(url)

        self.assertEqual(response.data, NON_EXISTENT_RESOURCE_ERROR_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_id_in_invalid_format(self):
        invalid_format_id = "this_is_totally_invalid"
        url = _get_two_citizens_url(self.citizen_1.id, invalid_format_id)

        response = self.client.get(url)

        self.assertEqual(response.data, INVALID_ID_FORMAT_ERROR_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_get_requests_allowed(self):
        url = _get_two_citizens_url(self.citizen_1.id, self.citizen_2.id)

        for http_method in [self.client.post, self.client.put, self.client.delete]:
            with self.subTest(http_method.__name__):
                response = self.client.post(url)

                self.assertEqual(response.status_code,
                                 status.HTTP_405_METHOD_NOT_ALLOWED)


class CompaniesViewTest(APITestCase):

    def setUp(self):
        self.company = Company.objects.create(name='TEST COMPANY')

        self.TEST_CITIZEN_1_DATA = {
            'id': 1,
            'name': "Test Citizen 1",
            'age': 51,
            'company': self.company,
        }
        self.TEST_CITIZEN_2_DATA = {
            'id': 2,
            'name': "Test Citizen 2",
            'age': 52,
            'company': self.company,
        }

        self.citizen_1 = _create_test_citizen(**self.TEST_CITIZEN_1_DATA)
        self.citizen_2 = _create_test_citizen(**self.TEST_CITIZEN_2_DATA)

    def test_happy_path(self):
        url = _get_company_employees_url(self.company.id)

        response = self.client.get(url)

        self.assertEqual(
            response.data,
            {
                'employees': [
                    'http://testserver' + _get_single_citizen_url(self.citizen_1.id),
                    'http://testserver' + _get_single_citizen_url(self.citizen_2.id),
                ]
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_company_has_not_employees(self):
        empty_company = Company.objects.create(name='EMPTY COMPANY')
        url = _get_company_employees_url(empty_company.id)

        response = self.client.get(url)

        self.assertEqual(response.data, NO_EMPLOYEES_ERROR_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_company_does_not_exist(self):
        non_existent_citizen_id = 42
        url = _get_company_employees_url(non_existent_citizen_id)

        response = self.client.get(url)

        self.assertEqual(response.data, NON_EXISTENT_RESOURCE_ERROR_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_id_in_invalid_format(self):
        invalid_format_id = "this_is_totally_invalid"
        url = _get_company_employees_url(invalid_format_id)

        response = self.client.get(url)

        self.assertEqual(response.data, INVALID_ID_FORMAT_ERROR_PAYLOAD)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_get_requests_allowed(self):
        url = _get_company_employees_url(self.company.id)

        for http_method in [self.client.post, self.client.put, self.client.delete]:
            with self.subTest(http_method.__name__):
                response = self.client.post(url)

                self.assertEqual(response.status_code,
                                 status.HTTP_405_METHOD_NOT_ALLOWED)


# Test helper methods below.
# Might be extracted to a separate module if they are to be reused.

def _create_test_citizen(**kwargs):
    eye_color, _ = EyeColor.objects.get_or_create(color_name='blue')
    citizen_data = {
        '_id': kwargs.get('id', '0'),
        'id': 0,
        'guid': kwargs.get('id', '0'),
        'has_died': False,
        'picture_url': '',
        'name': 'Test Citizen',
        'age': 30,
        'email': 'testcitizen1@email.com',
        'about': 'About',
        'greeting': 'Hello',
        'gender_code': 1,
        'registered_at': now(),
        'balance_in_cents': 0,
        'eye_color': eye_color,
        'phone_number': '+1 (123) 456 789',
        'address': Address.objects.create(
            street_address='1 Street',
            city_name='City',
            state_name='State',
            post_code='2017'
        ),
        **kwargs
    }

    return Citizen.objects.create(**citizen_data)


def _get_single_citizen_url(citizen_id):
    return reverse('single_citizen', kwargs={"citizen_id": citizen_id})


def _get_two_citizens_url(citizen_a_id, citizen_b_id):
    return reverse(
        'two_citizens',
        kwargs={"citizen_a_id": citizen_a_id, "citizen_b_id": citizen_b_id}
    )


def _get_company_employees_url(company_id):
    return reverse('company_employees', kwargs={"company_id": company_id})
