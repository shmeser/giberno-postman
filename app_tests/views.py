import random

from django.db import transaction
from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from app_market.models import Distributor, Shop, Vacancy, Shift, VacancyAppeal
from app_sockets.controllers import SocketController
from app_users.enums import AccountType
from app_users.models import UserProfile
from backend.controllers import PushController
from backend.utils import get_request_body, chained_get


class GetUserTokenTestAPIView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        user = UserProfile.objects.get(id=self.kwargs['pk'])
        return Response(str(RefreshToken.for_user(user=user).access_token))


class SendTestPush(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        body = get_request_body(request)
        PushController().send_notification(
            users_to_send=[request.user],
            title=chained_get(body, 'title') or '',
            message=chained_get(body, 'message') or '',
            action=chained_get(body, 'action'),
            subject_id=chained_get(body, 'subject_id'),
            notification_type=chained_get(body, 'notification_type'),
            icon_type=chained_get(body, 'icon_type'),
        )

        # Отправка уведомления по сокетам
        SocketController(request.user).send_single_notification({
            'title': chained_get(body, 'title') or '',
            'message': chained_get(body, 'message') or '',
            'action': chained_get(body, 'action'),
            'subjectId': chained_get(body, 'subject_id'),
            'notificationType': chained_get(body, 'notification_type'),
            'iconType': chained_get(body, 'icon_type'),
        })
        return Response(camelize(body), status=status.HTTP_200_OK)


class SeedDataForMarketAppAPIView(APIView):
    permission_classes = []

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        limit = 10
        multiply = 50

        if UserProfile.objects.count() < limit * multiply:
            for item in range(limit * multiply):
                UserProfile.objects.create(account_type=random.choice([1, 2, 3]))

        users = UserProfile.objects.all()

        print('Users seed complete')

        if Distributor.objects.count() < limit:
            for item in range(limit):
                Distributor.objects.create(title=f"""Distributor {item}""")

        print('Distributors seed complete')
        distributors = Distributor.objects.all()

        if Shop.objects.count() < limit * limit:
            for item in range(limit * limit):
                Shop.objects.create(
                    distributor=random.choice(distributors),
                    title=f"""Shop {item}"""
                )

        print('Shops seed complete')
        shops = Shop.objects.all()

        for user in users:
            if user.account_type == AccountType.MANAGER:
                user.manager_shops.add(random.choice(shops))
                user.save()

        if Vacancy.objects.count() < limit * limit:
            for item in range(limit * limit):
                Vacancy.objects.create(
                    shop=random.choice(shops),
                    title=f"""Vacancy {item}"""
                )

        print('Vacancies seed complete')
        vacancies = Vacancy.objects.all()

        if Shift.objects.count() < limit * multiply:
            for item in range(limit * multiply):
                vacancy = random.choice(vacancies)
                shop = vacancy.shop
                Shift.objects.create(vacancy=vacancy, shop=shop)

        print('Shifts seed complete')
        shifts = Shift.objects.all()

        self_employed_users = users.filter(account_type=AccountType.SELF_EMPLOYED)
        VacancyAppeal.objects.all().delete()
        for user in self_employed_users:
            VacancyAppeal.objects.create(user=user, vacancy=random.choice(vacancies))

        print('VacancyAppeal seed complete')
        return Response('seed complete')


class GetUsersIdListByTypeAPIView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return Response(UserProfile.objects.filter(account_type=self.kwargs.get('type')).values('id'))
