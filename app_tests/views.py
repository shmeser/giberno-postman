import uuid
from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from djangorestframework_camel_case.util import camelize
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from app_market.enums import TransactionType, TransactionStatus, Currency, TransactionKind
from app_market.versions.v1_0.repositories import OrdersRepository, TransactionsRepository
from app_sockets.controllers import SocketController
from app_users.enums import NotificationAction, NotificationIcon, NotificationType
from app_users.models import UserProfile
from app_users.versions.v1_0.repositories import CardsRepository
from app_users.versions.v1_0.serializers import CardsValidator, CardsSerializer
from backend.controllers import PushController
from backend.errors.enums import RESTErrors
from backend.errors.http_exceptions import HttpException
from backend.fields import DateTimeField
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


class MoneyValidator(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1, max_value=1000000)
    date = DateTimeField()
    taxes = serializers.IntegerField(required=False, min_value=1, max_value=1000000)
    insurance = serializers.IntegerField(required=False, min_value=1, max_value=1000000)


class TestMoneyPay(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        body = get_request_body(request)
        validator = MoneyValidator(data=body)

        if validator.is_valid(raise_exception=True):
            user_ct = ContentType.objects.get_for_model(request.user)

            amount = validator.validated_data.get('amount')

            pay = OrdersRepository.create_transaction(
                amount=amount,
                t_type=TransactionType.TEST.value,
                to_ct=user_ct,
                to_ct_name=user_ct.model,
                to_id=request.user.id,
                comment='Тестовое начисление зарплаты',
                **{
                    'status': TransactionStatus.COMPLETED.value,
                    'from_currency': Currency.RUB.value,
                    'to_currency': Currency.RUB.value,
                    'kind': TransactionKind.PAY.value,
                }
            )
            pay.created_at = validator.validated_data.get('date')
            pay.save()

            # Налоги
            if validator.validated_data.get('taxes'):
                tax = OrdersRepository.create_transaction(
                    amount=validator.validated_data.get('taxes'),
                    t_type=TransactionType.TEST.value,
                    from_ct=user_ct,
                    from_ct_name=user_ct.model,
                    from_id=request.user.id,
                    comment='Тестовое списание налогов',
                    **{
                        'status': TransactionStatus.COMPLETED.value,
                        'from_currency': Currency.RUB.value,
                        'to_currency': Currency.RUB.value,
                        'kind': TransactionKind.TAXES.value,
                    }
                )
                tax.created_at = validator.validated_data.get('date')
                tax.save()

            # Страховка
            if validator.validated_data.get('insurance'):
                ins = OrdersRepository.create_transaction(
                    amount=validator.validated_data.get('insurance'),
                    t_type=TransactionType.TEST.value,
                    from_ct=user_ct,
                    from_ct_name=user_ct.model,
                    from_id=request.user.id,
                    comment='Тестовое списание средств за страховку',
                    **{
                        'status': TransactionStatus.COMPLETED.value,
                        'from_currency': Currency.RUB.value,
                        'to_currency': Currency.RUB.value,
                        'kind': TransactionKind.INSURANCE.value,
                    }
                )
                ins.created_at = validator.validated_data.get('date')
                ins.save()

            TransactionsRepository(request.user).recalculate_money(currency=Currency.RUB.value)

            title = 'Начислены деньги'
            message = f'Начисление {amount} рублей на Ваш счет.'
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


class TestMoneyReward(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        body = get_request_body(request)
        validator = MoneyValidator(data=body)

        if validator.is_valid(raise_exception=True):
            user_ct = ContentType.objects.get_for_model(request.user)

            amount = validator.validated_data.get('amount')

            pay = OrdersRepository.create_transaction(
                amount=amount,
                t_type=TransactionType.TEST.value,
                to_ct=user_ct,
                to_ct_name=user_ct.model,
                to_id=request.user.id,
                comment='Тестовое начисление вознаграждения за друга',
                **{
                    'status': TransactionStatus.COMPLETED.value,
                    'from_currency': Currency.RUB.value,
                    'to_currency': Currency.RUB.value,
                    'kind': TransactionKind.FRIEND_REWARD.value,
                }
            )
            pay.created_at = validator.validated_data.get('date')
            pay.save()

            TransactionsRepository(request.user).recalculate_money(currency=Currency.RUB.value)

            title = 'Начислены деньги'
            message = f'Начисление вознаграждения за друга в размере {amount} рублей.'
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


class TestMoneyPenalty(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        body = get_request_body(request)
        validator = MoneyValidator(data=body)

        if validator.is_valid(raise_exception=True):
            user_ct = ContentType.objects.get_for_model(request.user)

            amount = validator.validated_data.get('amount')

            pay = OrdersRepository.create_transaction(
                amount=amount,
                t_type=TransactionType.TEST.value,
                from_ct=user_ct,
                from_ct_name=user_ct.model,
                from_id=request.user.id,
                comment='Тестовый штраф',
                **{
                    'status': TransactionStatus.COMPLETED.value,
                    'from_currency': Currency.RUB.value,
                    'to_currency': Currency.RUB.value,
                    'kind': TransactionKind.PENALTY.value,
                }
            )
            pay.created_at = validator.validated_data.get('date')
            pay.save()

            TransactionsRepository(request.user).recalculate_money(currency=Currency.RUB.value)

            title = 'Списаны деньги'
            message = f'Вам выписан штраф и списаны средства в размере {amount} рублей.'
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


class TestCards(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        body = get_request_body(request)
        validator = CardsValidator(data=body)

        if validator.is_valid(raise_exception=True):
            card = CardsRepository(me=request.user).add_card(real_pan=body.get('pan'), data=validator.validated_data)
            serializer = CardsSerializer(card, many=False)
            return Response(camelize(serializer.data), status=status.HTTP_200_OK)
