from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from citizens.models import Citizen, Company
from citizens.rest.constants import INVALID_ID_FORMAT_ERROR_PAYLOAD, \
    NO_EMPLOYEES_ERROR_PAYLOAD
from citizens.rest.constants import NON_EXISTENT_RESOURCE_ERROR_PAYLOAD
from citizens.rest.serializers import CitizenSerializer, MultiCitizenSerializer, \
    CompanySerializer
from citizens.use_cases import get_common_live_brown_eyed_friends


class SingleCitizenDetailsView(APIView):
    @staticmethod
    def get(request, citizen_id):
        error_response = _validate_params_format(citizen_id)

        if error_response:
            return error_response

        try:
            citizen = Citizen.objects.get(id=citizen_id)
        except Citizen.DoesNotExist:
            return Response(
                data=NON_EXISTENT_RESOURCE_ERROR_PAYLOAD,
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CitizenSerializer(citizen)
        return Response(serializer.data)


class TwoCitizensDetailsView(APIView):
    @staticmethod
    def get(request, citizen_a_id, citizen_b_id):
        error_response = _validate_params_format(citizen_a_id, citizen_b_id)

        if error_response:
            return error_response

        citizens = Citizen.objects.filter(id__in=[citizen_a_id, citizen_b_id])
        if len(citizens) != 2:
            return Response(
                data=NON_EXISTENT_RESOURCE_ERROR_PAYLOAD,
                status=status.HTTP_404_NOT_FOUND
            )

        citizens_serializer = MultiCitizenSerializer(citizens, many=True)

        common_friends = get_common_live_brown_eyed_friends(*citizens)
        common_friends_serializer = MultiCitizenSerializer(common_friends, many=True)

        data = {
            'citizens': citizens_serializer.data,
            'common_live_brown_eyed_friends': common_friends_serializer.data
        }

        return Response(data)


class CompanyEmployeesView(APIView):
    @staticmethod
    def get(request, company_id):
        error_response = _validate_params_format(company_id)

        if error_response:
            return error_response

        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response(
                data=NON_EXISTENT_RESOURCE_ERROR_PAYLOAD,
                status=status.HTTP_404_NOT_FOUND
            )

        if not company.citizen_set.exists():
            return Response(
                data=NO_EMPLOYEES_ERROR_PAYLOAD,
                status=status.HTTP_204_NO_CONTENT
            )

        serializer = CompanySerializer(company, context={'request': request})
        return Response(serializer.data)


def _validate_params_format(*args):
    """All parameters must be integers"""

    for param in args:
        try:
            int(param)
        except ValueError:
            return Response(
                data=INVALID_ID_FORMAT_ERROR_PAYLOAD,
                status=status.HTTP_400_BAD_REQUEST
            )
