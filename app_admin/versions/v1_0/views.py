from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from app_admin.versions.v1_0.repositories import UserAccessRepository
from app_admin.versions.v1_0.serializers import AccessSerializer, ContentTypeSerializer, StaffSerializer
from app_users.permissions import IsAdminOrManager
from backend.mappers import RequestMapper
from backend.utils import get_request_body


class Staff(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        paginator = RequestMapper.pagination(request)
        data, count = UserAccessRepository().get_staff(paginator)
        serialized = StaffSerializer(data, many=True)
        return Response(camelize(serialized.data), headers={'total-count': count})


class AccessContentTypes(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        data = UserAccessRepository().get_available_content_types()
        serialized = ContentTypeSerializer(data, many=True)
        return Response(camelize(serialized.data))


class UsersAccess(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        data = UserAccessRepository().get_access_rights(request.query_params.get('user'))
        serialized = AccessSerializer(data, many=True)
        return Response(camelize(serialized.data))

    @staticmethod
    def post(request, **kwargs):
        body = get_request_body(request)
        UserAccessRepository.add_access(body)
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class UserAccess(APIView):
    permission_classes = [IsAdminOrManager]

    @staticmethod
    def get(request, **kwargs):
        data = UserAccessRepository().get_by_id(kwargs.get('record_id'))
        serialized = AccessSerializer(data, many=False)
        return Response(camelize(serialized.data))

    @staticmethod
    def put(request, **kwargs):
        data = UserAccessRepository().get_by_id(kwargs.get('record_id'))
        serialized = AccessSerializer(data, many=False)
        return Response(camelize(serialized.data))

    @staticmethod
    def delete(request, **kwargs):
        data = UserAccessRepository().get_by_id(kwargs.get('record_id'))
        data.deleted = True
        data.save()
        return Response(None, status=status.HTTP_204_NO_CONTENT)
