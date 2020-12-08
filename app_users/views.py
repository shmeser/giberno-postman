from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.errors.http_exception import HttpException
from app_users.versions.v1_0 import views as v1_0


class Users(APIView):
    @staticmethod
    def get(request):
        if request.version in ['users_1_0']:
            pass
        return JsonResponse({
        })
