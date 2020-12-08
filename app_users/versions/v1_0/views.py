# from django.http import JsonResponse
# from djangorestframework_camel_case.util import camelize, underscoreize
# from drf_yasg.utils import swagger_auto_schema
# from rest_framework import status
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import AllowAny, IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.views import APIView
#
# from backend.errors.errors import Errors
# from backend.errors.http_exception import HttpException
# from backend.utils import get_body_in_request, milliseconds_to_datetime
# from media.mappers import RequestToMediaEntity
# from media.repositories import MediaRepository
# from subscriptions.tasks import check_subscription
# from users.enums import GenderEnum
# from users.permissions import FilledProfilePermission
# from users.repositories import UsersRepository
# from users.serializers import UserSerializer, UserPatchSerializer
#
#
# class User(APIView):
#     permission_classes = (IsAuthenticated,)
#     serializer_class = UserSerializer
#     nullable_fields = {
#         'birth_date',
#         'phone_number',
#         'avatar',
#         'sex',
#         'height',
#         'weight',
#         'daily_calorie_intake',
#         'city',
#         'religion',
#         'vegetarianism',
#         'invited_by',
#         'email'
#     }
#
#     def get(self, request):
#         FilledProfilePermission().has_permission(request)
#         check_subscription(request.user.id)
#         user_data = self.serializer_class(request.user)
#         return Response(camelize(user_data.data), status=status.HTTP_200_OK)
#
#     def put(self, request):
#         data = get_body_in_request(request)
#
#         {data.setdefault(nullable_field) for nullable_field in self.nullable_fields}
#
#         user_data = self.serializer_class(request.user, data=data)
#         user_data.is_valid(raise_exception=True)
#         user_data.save()
#         return Response(camelize(user_data.data), status=status.HTTP_200_OK)
#
#     def patch(self, request):
#         data = get_body_in_request(request)
#
#         serializer = UserPatchSerializer(request.user, data=data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(camelize(serializer.data), status=status.HTTP_200_OK)
#
#     def delete(self, request):
#         UsersRepository().delete_profile(request.user)
#         return JsonResponse({'status': 200})
#
#     @staticmethod
#     @swagger_auto_schema(
#         responses={
#             status.HTTP_200_OK: UserSerializer,
#             Errors.MESSAGE_TYPE_ERROR.value: Errors.MESSAGE_TYPE_ERROR.name,
#             Errors.BAD_REQUEST.value: Errors.BAD_REQUEST.name,
#             Errors.UUID_UNIQUE_ERROR.value: Errors.UUID_UNIQUE_ERROR.name
#         },
#         method='PATCH',
#         tags=['User']
#     )
#     @api_view(['PATCH'])
#     def upload_avatar(request, **kwargs):
#         media_entity = RequestToMediaEntity.map(request)
#         media = MediaRepository.create_media(media_entity)
#
#         user = UsersRepository().update(request.user.id, avatar=media)
#         user_data = UserSerializer(user)
#
#         return Response(camelize(user_data.data), status=status.HTTP_200_OK)
#
#
# @swagger_auto_schema(responses={status.HTTP_200_OK: 'daily_calories_intake'}, method='GET', tags=['User'])
# @api_view(['GET'])
# @permission_classes([AllowAny])
# def calculate_calories(request, **kwargs):
#     serializer = UserSerializer()
#     REQUIRED_FIELDS = ['height', 'weight']
#     fields = underscoreize(request.query_params.copy())
#
#     data = {i: float(fields.get(i)) for i in REQUIRED_FIELDS}
#     birth_date_ts_str = fields.get('birth_date', None)
#
#     serializer.validate_weight(data.get('weight'))
#     serializer.validate_height(data.get('height'))
#
#     if all([True if i in fields else False for i in REQUIRED_FIELDS]):
#         try:
#             sex = int(fields.get('sex', GenderEnum.MALE.value))
#         except ValueError as e:
#             raise HttpException(status_code=Errors.BAD_REQUEST.value, detail=e)
#         if not birth_date_ts_str or birth_date_ts_str.lower() == 'null':  # Если пустая строка, null или None
#             data['birth_date'] = None
#         else:
#             data['birth_date'] = milliseconds_to_datetime(int(float(birth_date_ts_str)))
#         calories = UsersRepository().calculate_calories(sex, data)
#         return Response(camelize({'daily_calories_intake': calories}), status=status.HTTP_200_OK)
#     return Response(camelize({'daily_calories_intake': 0}), status=status.HTTP_200_OK)
