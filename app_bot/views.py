from django.views import View
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .versions.v1_0 import views as v1_0


class TelegramBotView(View):
    @staticmethod
    def post(request, **kwargs):
        return v1_0.TelegramBotView().post(request, **kwargs)


class TestView(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def get(request):
        return v1_0.TestView().get(request)
