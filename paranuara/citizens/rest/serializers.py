from rest_framework import serializers

from citizens.models import Citizen, Food, Company


class CitizenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Citizen
        fields = ['username', 'age', 'fruits', 'vegetables']

    username = serializers.ReadOnlyField(source="name")
    fruits = serializers.SerializerMethodField()
    vegetables = serializers.SerializerMethodField()

    @staticmethod
    def get_fruits(citizen):
        return list(
            citizen.favourite_food.filter(type=Food.FRUIT)
                .values_list('name', flat=True)
        )

    @staticmethod
    def get_vegetables(citizen):
        return list(
            citizen.favourite_food.filter(type=Food.VEGETABLE)
                .values_list('name', flat=True)
        )


class MultiCitizenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Citizen
        fields = ['username', 'age', 'address', 'phone_number']

    username = serializers.ReadOnlyField(source="name")
    address = serializers.SerializerMethodField()

    def get_address(self, citizen):
        return str(citizen.address)


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['employees']

    employees = serializers.HyperlinkedRelatedField(
        source='citizen_set',
        view_name='single_citizen',
        many=True,
        read_only=True,
        lookup_url_kwarg='citizen_id',
    )
