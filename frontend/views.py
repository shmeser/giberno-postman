import logging
import os

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from app_media.enums import MimeTypes
from backend.errors.enums import RESTErrors


# from backend.utils import get_request_body


class FrontendAppView(View):
    """
    Serves the compiled frontend entry point (only works if you have run `npm
    run build`).
    """

    @staticmethod
    def get(request):
        try:
            with open(os.path.join(settings.REACT_APP_DIR, 'build', 'index.html'), encoding="utf_8_sig") as f:
                return HttpResponse(f.read())
        except FileNotFoundError:
            logging.exception('Production build of app not found')
            return HttpResponse(
                """
                Данный url используется фронтендом.
                Необходимо поместить скомпилированный фронтенд в папку frontend/build.
                """,
                status=RESTErrors.NOT_FOUND
            )


class AgreementView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        elif self.request.method == "POST":
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    @staticmethod
    def get(request):
        try:
            with open(os.path.join(settings.REACT_APP_DIR, 'public', 'agreement.pdf'), 'rb') as f:
                return HttpResponse(f.read(), content_type=MimeTypes.PDF.value)
        except FileNotFoundError:
            logging.exception('Production build of app not found')
            return HttpResponse(
                """
                Не найден файл пользовательского соглашения
                """,
                status=RESTErrors.NOT_FOUND)


class PolicyView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        elif self.request.method == "POST":
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    @staticmethod
    def get(request):
        try:
            with open(os.path.join(settings.REACT_APP_DIR, 'public', 'policy.pdf'), 'rb') as f:
                return HttpResponse(f.read(), content_type=MimeTypes.PDF.value)
        except FileNotFoundError:
            logging.exception('Production build of app not found')
            return HttpResponse(
                """
                Не найден файл политики конфиденциальности
                """,
                status=RESTErrors.NOT_FOUND
            )


class TermsView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        elif self.request.method == "POST":
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    @staticmethod
    def get(request):
        try:
            with open(os.path.join(settings.REACT_APP_DIR, 'public', 'terms.pdf'), 'rb') as f:
                return HttpResponse(f.read(), content_type=MimeTypes.PDF.value)
        except FileNotFoundError:
            logging.exception('Production build of app not found')
            return HttpResponse(
                """
                Не найден файл условий использования
                """,
                status=RESTErrors.NOT_FOUND)

    @staticmethod
    def post(request):
        request.user.terms_accepted = True
        request.user.save()
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class DocumentsView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        elif self.request.method == "POST":
            return [IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    @staticmethod
    def post(request):
        request.user.terms_accepted = True
        request.user.policy_accepted = True
        request.user.agreement_accepted = True
        request.user.save()
        return Response(None, status=status.HTTP_204_NO_CONTENT)
