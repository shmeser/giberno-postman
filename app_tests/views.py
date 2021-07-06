import random
import uuid
from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from app_market.enums import TransactionType, TransactionStatus
from app_market.models import Distributor, Shop, Vacancy, Shift
from app_market.versions.v1_0.repositories import OrdersRepository
from app_sockets.controllers import SocketController
from app_users.enums import AccountType, NotificationAction, NotificationIcon, NotificationType
from app_users.models import UserProfile
from backend.controllers import PushController
from backend.errors.enums import RESTErrors
from backend.errors.http_exceptions import HttpException
from backend.utils import get_request_body


class GetUserTokenTestAPIView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        user = UserProfile.objects.get(id=self.kwargs['pk'])
        token = RefreshToken.for_user(user=user)
        access_token = token.access_token
        access_token.set_exp(lifetime=timedelta(days=3650))
        return Response(str(access_token))


class SendTestPush(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        body = get_request_body(request)
        title = body.pop('title', '')
        message = body.pop('message', '')
        action = body.pop('action', None)
        subject_id = body.pop('subject_id', None)
        notification_type = body.pop('notification_type', None)
        icon_type = body.pop('icon_type', None)

        # uuid для массовой рассылки оповещений,
        # у пользователей в бд будут созданы оповещения с одинаковым uuid
        # uuid необходим на клиенте для фильтрации одинаковых данных, полученных по 2 каналам - сокеты и пуши
        common_uuid = uuid.uuid4()

        PushController().send_notification(
            users_to_send=[request.user],
            title=title,
            message=message,
            common_uuid=common_uuid,
            action=action,
            subject_id=subject_id,
            notification_type=notification_type,
            icon_type=icon_type,
            **body  # оставшиеся поля передаем как kwargs
        )

        # Отправка уведомления по сокетам
        SocketController(request.user, version='1.0').send_notification_to_my_connection({
            'title': title,
            'message': message,
            'uuid': str(common_uuid),
            'action': action,
            'subjectId': subject_id,
            'notificationType': notification_type,
            'iconType': icon_type,
        })
        return Response(camelize({
            'uuid': common_uuid,
            'title': title,
            'message': message,
            'action': action,
            'subject_id': subject_id,
            'notification_type': notification_type,
            'icon_type': icon_type,
            **body
        }), status=status.HTTP_200_OK)


class TestBonusesDeposit(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        body = get_request_body(request)
        amount = body.get("amount", 0)

        if amount <= 0:
            raise HttpException(status_code=RESTErrors.BAD_REQUEST.value, detail='amount должен быть положительным')

        user_ct = ContentType.objects.get_for_model(request.user)
        OrdersRepository.create_transaction(
            amount=amount,
            t_type=TransactionType.TEST.value,
            to_ct=user_ct,
            to_ct_name=user_ct.model,
            to_id=request.user.id,
            comment='Тестовое начисление бонусов',
            **{
                'status': TransactionStatus.COMPLETED.value
            }
        )

        request.user.bonus_balance += amount
        request.user.save()

        title = 'Начислены бонусы'
        message = f'Начисление {amount} очков славы'
        action = NotificationAction.USER.value
        subject_id = request.user.id
        notification_type = NotificationType.SYSTEM.value
        icon_type = NotificationIcon.DEFAULT.value

        # uuid для массовой рассылки оповещений,
        # у пользователей в бд будут созданы оповещения с одинаковым uuid
        # uuid необходим на клиенте для фильтрации одинаковых данных, полученных по 2 каналам - сокеты и пуши
        common_uuid = uuid.uuid4()

        PushController().send_notification(
            users_to_send=[request.user],
            title=title,
            message=message,
            common_uuid=common_uuid,
            action=action,
            subject_id=subject_id,
            notification_type=notification_type,
            icon_type=icon_type,
        )

        # Отправка уведомления по сокетам
        SocketController(request.user, version='1.0').send_notification_to_my_connection({
            'title': title,
            'message': message,
            'uuid': str(common_uuid),
            'action': action,
            'subjectId': subject_id,
            'notificationType': notification_type,
            'iconType': icon_type,
        })

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class SeedDataForMarketAppAPIView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        limit = 5
        multiply = 10

        with transaction.atomic():
            # USERS SEED
            if UserProfile.objects.count() < limit * multiply:
                for item in range(limit * multiply):
                    UserProfile.objects.create(account_type=random.choice([1, 2, 3]))

            users = UserProfile.objects.all()

            print('Users seed complete')

            # DISTRIBUTORS SEED
            if Distributor.objects.count() < limit:
                for item in range(limit):
                    Distributor.objects.create(title=f"""Distributor {item}""")

            print('Distributors seed complete')
            distributors = Distributor.objects.all()

            # SHOPS SEED
            if Shop.objects.count() < limit * limit:
                for item in range(limit * limit):
                    Shop.objects.create(
                        distributor=random.choice(distributors),
                        title=f"""Shop {item + 1}"""
                    )

            print('Shops seed complete')
            shops = Shop.objects.all()

            # SET SHOPS FOR MANAGERS
            for user in users.filter(account_type=AccountType.MANAGER):
                shop = random.choice(shops)
                user.shops.add(shop)
                user.distributors.add(shop.distributor)
                user.save()

            # SET SHOPS FOR SECURITY
            for user in users.filter(account_type=AccountType.SECURITY):
                user.shops.add(random.choice(shops))
                user.save()

            # VACANCIES SEED
            if Vacancy.objects.count() < limit * limit:
                for item in range(limit * limit):
                    Vacancy.objects.create(
                        shop=random.choice(shops),
                        title=f"""Vacancy {item + 1}"""
                    )

            print('Vacancies seed complete')
            vacancies = Vacancy.objects.all()

            # SHIFTS SEED
            if Shift.objects.count() < limit * multiply:
                for item in range(limit * multiply):
                    vacancy = random.choice(vacancies)
                    shop = vacancy.shop
                    Shift.objects.create(vacancy=vacancy, shop=shop)

            print('Shifts seed complete')
            shifts = Shift.objects.all()

            # SET APPEALS FOR SELF EMPLOYED USERS
            # ShiftAppeal.objects.all().delete()
            # for user in users.filter(account_type=AccountType.SELF_EMPLOYED):
            #     ShiftAppeal.objects.create(applier=user, shift=random.choice(shifts))
            print('ShiftAppeal seed complete')

            # USER SHIFTS SEED
            # shift_appeals = ShiftAppeal.objects.all()
            # for shift_appeal in shift_appeals:
            #     UserShift.objects.create(
            #         user=shift_appeal.applier,
            #         shift=shift_appeal.shift
            #     )
            #
            # print('UserShifts seed complete')

        return Response('seed complete')


class GetUsersIdListByTypeAPIView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return Response(UserProfile.objects.filter(account_type=self.kwargs.get('type')).values('id'))
