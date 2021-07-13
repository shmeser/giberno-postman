import uuid

from django.utils.timezone import now
from djangorestframework_camel_case.util import camelize, underscoreize
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from app_feedback.versions.v1_0.repositories import ReviewsRepository
from app_feedback.versions.v1_0.serializers import POSTReviewSerializer, ReviewModelSerializer, \
    POSTReviewByManagerSerializer, POSTShopReviewSerializer, DistributorReviewsSerializer, \
    VacancyReviewsSerializer, ShopVacanciesReviewsSerializer
from app_market.enums import AppealCancelReason, ShiftAppealStatus
from app_market.utils import QRHandler, send_socket_event_on_appeal_statuses
from app_market.versions.v1_0.repositories import VacanciesRepository, ProfessionsRepository, SkillsRepository, \
    DistributorsRepository, ShopsRepository, ShiftsRepository, ShiftAppealsRepository, \
    MarketDocumentsRepository, PartnersRepository, AchievementsRepository, AdvertisementsRepository, OrdersRepository, \
    CouponsRepository, TransactionsRepository
from app_market.versions.v1_0.serializers import QRCodeSerializer, VacanciesClusterSerializer, \
    ShiftAppealsSerializer, VacanciesWithAppliersForManagerSerializer, ShiftAppealCreateSerializer, \
    ShiftsWithAppealsSerializer, ShiftConditionsSerializer, ShiftForManagersSerializer, \
    ShiftAppealsForManagersSerializer, VacancyForManagerSerializer, ConfirmedWorkersShiftsSerializer, \
    ConfirmedWorkerProfessionsSerializer, ConfirmedWorkerDatesSerializer, ConfirmedWorkerSerializer, \
    ManagerAppealCancelReasonSerializer, SecurityPassRefuseReasonSerializer, FireByManagerReasonSerializer, \
    ProlongByManagerReasonSerializer, QRCodeCompleteSerializer, ShiftAppealCompleteSerializer, \
    ConfirmedWorkerSettingsValidator, PartnersSerializer, CategoriesSerializer, AchievementsSerializer, \
    AdvertisementsSerializer, OrdersSerializer, CouponsSerializer, PartnerConditionsSerializer, FinancesSerializer, \
    FinancesValiadator
from app_market.versions.v1_0.serializers import VacancySerializer, ProfessionSerializer, SkillSerializer, \
    DistributorsSerializer, ShopSerializer, VacanciesSerializer, ShiftsSerializer
from app_sockets.controllers import SocketController
from app_users.enums import NotificationAction, NotificationType, NotificationIcon
from app_users.versions.v1_0.repositories import ProfileRepository, MoneyRepository
from app_users.versions.v1_0.serializers import MoneySerializer
from backend.api_views import BaseAPIView
from backend.controllers import PushController
from backend.entity import Error
from backend.errors.enums import ErrorsCodes, RESTErrors
from backend.errors.http_exceptions import CustomException, HttpException
from backend.mappers import RequestMapper, DataMapper
from backend.mixins import CRUDAPIView
from backend.utils import get_request_body, chained_get, get_request_headers, timestamp_to_datetime, \
    get_timezone_name_by_geo


class Distributors(CRUDAPIView):
    serializer_class = DistributorsSerializer
    repository_class = DistributorsRepository
    allowed_http_methods = ['get']

    filter_params = {
        'search': 'title__istartswith',
    }

    default_order_params = ['-vacancies_count']

    default_filters = {}

    order_params = {
        'id': 'id',
        'title': 'title',
        'vacancies': 'vacancies_count',
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)
        point, screen_diagonal_points, radius = RequestMapper().geo(request)

        if record_id:
            dataset = self.repository_class(point=point, me=request.user).get_by_id(record_id)
        else:
            dataset = self.repository_class(point=point, me=request.user).filter_by_kwargs(
                kwargs=filters, order_by=order_params, paginator=pagination
            )

            self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Shops(CRUDAPIView):
    serializer_class = ShopSerializer
    repository_class = ShopsRepository
    allowed_http_methods = ['get']

    filter_params = {
        'search': 'title__istartswith',
        'distributor': 'distributor_id',
    }

    default_order_params = []

    default_filters = {}

    order_params = {
        'id': 'id',
        'title': 'title',
        'distance': 'distance',
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)
        point, screen_diagonal_points, radius = RequestMapper().geo(request)

        if record_id:
            dataset = self.repository_class(point=point).get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class(point=point).filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Vacancies(CRUDAPIView):
    serializer_class = VacanciesSerializer
    repository_class = VacanciesRepository
    allowed_http_methods = ['get']

    filter_params = {
        'search': 'title__istartswith',
        'country': 'city__country__id',
        'city': 'city_id',
        'shop': 'shop_id',
        'price': 'price__gte',
        'radius': 'distance__lte'
    }

    # добавил параметры:
    # 'applied' на получение только тех вакансии на которые пользователь откликался
    # 'confirmed' на получение только тех вакансии которые подтвердил работодатель
    bool_filter_params = {
        'is_favourite': 'is_favourite',
        'is_hot': 'is_hot',
        'applied': 'appeals__user',
        'confirmed': 'appeals__confirmed'
    }

    array_filter_params = {
        # overlap - пересечение множеств - если передано несколько, то нужно любое из имеющихся
        'required_experience': 'required_experience__overlap',
        'work_time': 'work_time__overlap',
        'employment': 'employment__in',
    }

    default_order_params = [
        '-created_at'
    ]

    default_filters = {}

    order_params = {
        'free_count': 'free_count',
        'distance': 'distance',
        'title': 'title',
        'price': 'price',
        'created_at': 'created_at',
        'id': 'id'
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)
        point, screen_diagonal_points, radius = RequestMapper().geo(request)

        if record_id:
            self.serializer_class = VacancySerializer
            dataset = self.repository_class(
                point=point, me=request.user
            ).get_by_id(record_id)
            dataset.increment_views_count()
        else:
            self.many = True
            dataset = self.repository_class(
                point=point, screen_diagonal_points=screen_diagonal_points, me=request.user
            ).filter_by_kwargs(
                kwargs=filters, order_by=order_params, paginator=pagination
            )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class ShiftAppeals(CRUDAPIView):
    repository_class = ShiftAppealsRepository
    serializer_class = ShiftAppealsSerializer

    allowed_http_methods = ['get', 'post']

    filter_params = {
        'shift': 'shift_id',
        'vacancy': 'shift__vacancy_id'
    }

    bool_filter_params = {
    }

    array_filter_params = {
        'status': 'status__in'
    }

    default_order_params = [
        '-created_at'
    ]

    default_filters = {}

    order_params = {
        'time_start': 'time_start',
        'time_end': 'time_end',
        'created_at': 'created_at',
        'id': 'id'
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)
        point, screen_diagonal_points, radius = RequestMapper().geo(request)

        if record_id:
            dataset = self.repository_class(me=request.user, point=point).get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class(me=request.user, point=point).filter_by_kwargs(
                kwargs=filters, order_by=order_params, paginator=pagination
            )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = get_request_body(request)
        if self.repository_class(me=request.user).check_permission_for_appeal(data.get('shift')):
            serializer = ShiftAppealCreateSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                instance, created = self.repository_class(me=request.user).get_or_create(**serializer.validated_data)
                # Отправляем по сокетам смену status и job_status смз и менеджерам
                applier_sockets, managers_sockets, users_and_managers = self.repository_class \
                    .get_self_employed_and_managers_with_sockets(appeal=instance)

                send_socket_event_on_appeal_statuses(
                    appeal=instance, applier_sockets=applier_sockets, managers_sockets=managers_sockets
                )

                if created:
                    instance.qr_text = QRHandler(instance).create_qr_data()
                    instance.save()
                return Response(camelize(ShiftAppealsSerializer(instance=instance, many=False).data))
        else:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.VACANCY_OR_SHOP_CHAT_IS_BLOCKED)),
            ])

    def put(self, request, *args, **kwargs):
        serializer = ShiftAppealCreateSerializer(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            record_id = kwargs.get(self.urlpattern_record_id_name)
            instance = self.repository_class(me=request.user).update(record_id, **serializer.validated_data)

            # Отправляем по сокетам смену status и job_status смз и менеджерам
            applier_sockets, managers_sockets, users_and_managers = self.repository_class \
                .get_self_employed_and_managers_with_sockets(appeal=instance)

            send_socket_event_on_appeal_statuses(
                appeal=instance, applier_sockets=applier_sockets, managers_sockets=managers_sockets
            )

            return Response(camelize(ShiftAppealsSerializer(instance=instance, many=False).data))


class ShiftAppealCancel(CRUDAPIView):
    repository_class = ShiftAppealsRepository

    def post(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        data = get_request_body(request)
        reason = data.get('reason')
        if reason is not None and not AppealCancelReason.has_value(reason):
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.VALIDATION_ERROR)),
            ])

        appeal, is_confirmed_appeal_canceled = self.repository_class(me=request.user).cancel(
            record_id=record_id, reason=reason, text=data.get('text')
        )
        managers, sockets = VacanciesRepository.get_managers_and_sockets_for_vacancy(appeal.shift.vacancy)

        # Отправляем по сокетам смену status и job_status смз и менеджерам
        send_socket_event_on_appeal_statuses(
            appeal=appeal,
            applier_sockets=list(appeal.applier.sockets.all().values_list('socket_id', flat=True)) or [],
            managers_sockets=sockets
        )

        _WORKER_CANCELED_APPEAL_TITLE = 'Самозанятый отказался от вакансии'

        if is_confirmed_appeal_canceled and managers:
            title = _WORKER_CANCELED_APPEAL_TITLE
            message = f'К сожалению, работник {request.user.first_name} {request.user.last_name} отказался от вакансии {appeal.shift.vacancy.title}'
            action = NotificationAction.VACANCY.value
            subject_id = appeal.shift.vacancy_id
            notification_type = NotificationType.SYSTEM.value
            icon_type = NotificationIcon.WORKER_CANCELED_VACANCY.value

            # uuid для массовой рассылки оповещений,
            # у пользователей в бд будут созданы оповещения с одинаковым uuid
            # uuid необходим на клиенте для фильтрации одинаковых данных, полученных по 2 каналам - сокеты и пуши
            common_uuid = uuid.uuid4()

            PushController().send_notification(
                users_to_send=managers,
                title=title,
                message=message,
                common_uuid=common_uuid,
                action=action,
                subject_id=subject_id,
                notification_type=notification_type,
                icon_type=icon_type
            )

            # Отправка уведомления по сокетам
            SocketController(request.user, version='1.0').send_notification_to_many_connections(sockets, {
                'title': title,
                'message': message,
                'uuid': str(common_uuid),
                'action': action,
                'subjectId': subject_id,
                'notificationType': notification_type,
                'iconType': icon_type,
            })

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class ShiftAppealComplete(CRUDAPIView):
    repository_class = ShiftAppealsRepository

    def post(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        body = get_request_body(request) if request.body else {}
        serializer = ShiftAppealCompleteSerializer(data=body)
        if serializer.is_valid(raise_exception=True):
            appeal = self.repository_class(me=request.user).complete_appeal(
                record_id=record_id, **serializer.validated_data
            )
            # Отправляем по сокетам смену status и job_status смз и менеджерам
            applier_sockets, managers_sockets, users_and_managers = self.repository_class \
                .get_self_employed_and_managers_with_sockets(appeal=appeal)

            send_socket_event_on_appeal_statuses(
                appeal=appeal, applier_sockets=applier_sockets, managers_sockets=managers_sockets
            )

            return Response(None, status=status.HTTP_200_OK)


class ActiveVacanciesWithAppliersByDateForManagerListAPIView(CRUDAPIView):
    serializer_class = VacanciesWithAppliersForManagerSerializer
    repository_class = VacanciesRepository
    allowed_http_methods = ['get']

    array_filter_params = {
        'status': 'status__in'
    }

    default_filters = {
        'status__in': [ShiftAppealStatus.INITIAL.value, ShiftAppealStatus.CONFIRMED]
    }

    order_params = {
        'title': 'title',
        'created_at': 'created_at',
        'id': 'id'
    }

    def get(self, request, *args, **kwargs):
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)
        filters = RequestMapper(self).filters(request)

        current_date, next_day = RequestMapper(self).current_date_range(request)

        if not current_date:
            dataset = self.repository_class(me=request.user).queryset_by_manager(
                order_params=order_params, pagination=pagination
            )
        else:
            dataset = self.repository_class(me=request.user).queryset_filtered_by_current_date_range_for_manager(
                order_params=order_params, pagination=pagination, current_date=current_date, next_day=next_day
            )

        serialized = self.serializer_class(dataset, many=True, context={
            'me': request.user,
            'filters': filters,
            'current_date': current_date,
            'next_day': next_day,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class VacanciesActiveDatesForManagerListAPIView(CRUDAPIView):
    repository_class = VacanciesRepository
    allowed_http_methods = ['get']

    def get(self, request, *args, **kwargs):
        calendar_from, calendar_to = RequestMapper().calendar_range(request)
        active_dates = self.repository_class(
            me=request.user
        ).vacancies_active_dates_list_for_manager(
            calendar_from=calendar_from,
            calendar_to=calendar_to
        )
        response_data = {'active_dates': active_dates}
        return Response(camelize(response_data))


class SingleVacancyActiveDatesForManagerListAPIView(CRUDAPIView):
    repository_class = VacanciesRepository
    allowed_http_methods = ['get']

    def get(self, request, *args, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        calendar_from, calendar_to = RequestMapper().calendar_range(request)

        active_dates = self.repository_class(
            me=request.user
        ).single_vacancy_active_dates_list_for_manager(
            record_id=record_id,
            calendar_from=calendar_from,
            calendar_to=calendar_to
        )
        response_data = {'active_dates': active_dates}
        return Response(camelize(response_data))


class VacancyByManagerRetrieveAPIView(CRUDAPIView):
    serializer_class = VacancyForManagerSerializer
    repository_class = VacanciesRepository
    allowed_http_methods = ['get']

    def get(self, request, *args, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        dataset = self.repository_class(me=request.user).get_by_id_for_manager_or_security(record_id)

        serialized = self.serializer_class(dataset, many=False, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class VacancyShiftsWithAppealsListForManagerAPIView(CRUDAPIView):
    serializer_class = ShiftsWithAppealsSerializer
    repository_class = VacanciesRepository
    allowed_http_methods = ['get']
    array_filter_params = {
        'status': 'status__in'
    }
    default_filters = {
        'status__in': [ShiftAppealStatus.INITIAL.value, ShiftAppealStatus.CONFIRMED.value]
    }
    order_params = {}

    def get(self, request, **kwargs):
        pagination = RequestMapper.pagination(request)
        current_date, next_day = RequestMapper(self).current_date_range(request)
        filters = RequestMapper(self).filters(request) or dict()

        vacancy_id = kwargs.get('record_id') or request.query_params.get('vacancy')

        dataset = self.repository_class(me=request.user).vacancy_shifts_with_appeals_queryset(
            record_id=vacancy_id,
            pagination=pagination,
            current_date=current_date,
            next_day=next_day
        )

        serialized = self.serializer_class(dataset, many=True, context={
            'me': request.user,
            'current_date': current_date,
            'filters': filters,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class GetSingleAppealForManagerAPIView(CRUDAPIView):
    repository_class = ShiftAppealsRepository
    serializer_class = ShiftAppealsSerializer

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        appeal = self.repository_class(me=request.user).get_by_id_for_manager(record_id)
        return Response(self.serializer_class(instance=appeal).data)


class VacanciesClusteredMap(Vacancies):
    serializer_class = VacanciesClusterSerializer
    allowed_http_methods = ['get']

    def get(self, request, **kwargs):
        filters = RequestMapper(self).filters(request) or dict()
        order_params = RequestMapper(self).order(request)
        point, screen_diagonal_points, radius = RequestMapper().geo(request)

        self.many = True
        clustered = self.repository_class(point, screen_diagonal_points).map(kwargs=filters, order_by=order_params)

        clusters = DataMapper.clustering_raw_qs(clustered, 'cid')

        serialized = self.serializer_class(clusters, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Shifts(CRUDAPIView):
    serializer_class = ShiftsSerializer
    repository_class = ShiftsRepository
    allowed_http_methods = ['get']

    filter_params = {
        'vacancy': 'vacancy_id',
    }

    bool_filter_params = {
        'active_today': 'active_today',
    }

    array_filter_params = {
    }

    default_order_params = [
        '-created_at'
    ]

    default_filters = {}

    order_params = {
        'id': 'id'
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)
        calendar_from, calendar_to = RequestMapper().calendar_range(request)

        if record_id:
            self.serializer_class = ShiftsSerializer
            dataset = self.repository_class(calendar_from=calendar_from, calendar_to=calendar_to).get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class(calendar_from=calendar_from, calendar_to=calendar_to).filter_by_kwargs(
                kwargs=filters, order_by=order_params
            )
            dataset = dataset[pagination.offset:pagination.limit]

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class VacanciesStats(Vacancies):
    def get(self, request, **kwargs):
        filters = RequestMapper(self).filters(request) or dict()
        order_params = RequestMapper(self).order(request)

        point, screen_diagonal_points, radius = RequestMapper().geo(request)
        dataset = self.repository_class(
            point=point, screen_diagonal_points=screen_diagonal_points, me=request.user
        ).filter_by_kwargs(
            kwargs=filters, order_by=order_params
        )

        stats = self.repository_class().aggregate_stats(dataset)

        return Response(camelize({
            'all_prices': chained_get(stats, 'all_prices'),
            'all_counts': chained_get(stats, 'all_counts'),
            'result_count': chained_get(stats, 'result_count'),
        }), status=status.HTTP_200_OK)


class VacanciesDistributors(Vacancies):

    def get(self, request, **kwargs):
        filters = RequestMapper(self).filters(request) or dict()
        order_params = RequestMapper(self).order(request)
        pagination = RequestMapper.pagination(request)
        point, screen_diagonal_points, radius = RequestMapper().geo(request)
        dataset = self.repository_class(
            point=point, screen_diagonal_points=screen_diagonal_points, me=request.user
        ).filter_by_kwargs(
            kwargs=filters, order_by=order_params
        )

        distributors = self.repository_class(me=request.user).aggregate_distributors(dataset, pagination)
        serialized = DistributorsSerializer(distributors, many=True, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


@api_view(['GET'])
def vacancies_suggestions(request):
    pagination = RequestMapper.pagination(request)
    dataset = []
    search = request.query_params.get('search') if request.query_params else None
    if search:
        dataset = VacanciesRepository(me=request.user).get_suggestions(
            # trigram_similar Поиск с использованием pg_trgm на проиндексированном поле
            search=search,
            paginator=pagination
        )
    return Response(dataset, status=status.HTTP_200_OK)


@api_view(['GET'])
def similar_vacancies(request, **kwargs):
    pagination = RequestMapper.pagination(request)
    point, screen_diagonal_points, radius = RequestMapper().geo(request)
    vacancies = VacanciesRepository(
        point=point, screen_diagonal_points=screen_diagonal_points, me=request.user
    ).get_similar(
        kwargs.get('record_id'), pagination
    )

    serializer = VacanciesSerializer(vacancies, many=True, context={'me': request.user})
    return Response(camelize(serializer.data), status=status.HTTP_200_OK)


class ReviewsBaseAPIView(BaseAPIView):
    serializer_class = None
    get_request_repository_class = None
    post_request_repository_class = None

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        point, screen_diagonal_points, radius = RequestMapper().geo(request)

        if serializer.is_valid(raise_exception=True):
            self.post_request_repository_class(me=request.user).make_review(
                record_id=kwargs.get('record_id'),
                text=serializer.validated_data['text'],
                value=serializer.validated_data['value'],
                point=point
            )
            return Response(None, status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        pagination = RequestMapper.pagination(request)
        kwargs = {
            'target_id': kwargs['record_id'],
            'deleted': False
        }
        queryset = self.get_request_repository_class().filter_by_kwargs(kwargs=kwargs, paginator=pagination)
        return Response(camelize(ReviewModelSerializer(instance=queryset, many=True).data))


class VacancyReviewsAPIView(ReviewsBaseAPIView):
    serializer_class = POSTReviewSerializer
    get_request_repository_class = ReviewsRepository
    post_request_repository_class = VacanciesRepository

    def get(self, request, *args, **kwargs):
        pagination = RequestMapper.pagination(request)
        queryset = self.get_request_repository_class().get_vacancy_reviews(
            vacancy_id=kwargs.get('record_id'), pagination=pagination
        )
        return Response(camelize(VacancyReviewsSerializer(queryset, many=True).data))


class ShopReviewsAPIView(ReviewsBaseAPIView):
    serializer_class = POSTShopReviewSerializer
    get_request_repository_class = ReviewsRepository
    post_request_repository_class = ShopsRepository

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            self.post_request_repository_class(me=request.user).make_review(
                record_id=kwargs.get('record_id'),
                text=serializer.validated_data['text'],
                value=serializer.validated_data['value'],
                shift=serializer.validated_data.get('shift')
            )
            return Response(None, status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        pagination = RequestMapper.pagination(request)
        queryset = self.get_request_repository_class().get_shop_vacancies_reviews(
            shop_id=kwargs.get('record_id'), pagination=pagination
        )
        return Response(camelize(ShopVacanciesReviewsSerializer(queryset, many=True).data))


class DistributorReviewsAPIView(ReviewsBaseAPIView):
    serializer_class = POSTReviewSerializer
    get_request_repository_class = ReviewsRepository
    post_request_repository_class = DistributorsRepository

    def get(self, request, *args, **kwargs):
        pagination = RequestMapper.pagination(request)
        queryset = self.get_request_repository_class().get_distributor_reviews(
            distributor_id=kwargs.get('record_id'), pagination=pagination
        )
        return Response(camelize(DistributorReviewsSerializer(queryset, many=True).data))


class SelfEmployedUserReviewsByAdminOrManagerAPIView(ReviewsBaseAPIView):
    serializer_class = POSTReviewByManagerSerializer
    get_request_repository_class = ReviewsRepository
    post_request_repository_class = ProfileRepository

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        point, screen_diagonal_points, radius = RequestMapper().geo(request)

        if serializer.is_valid(raise_exception=True):
            self.post_request_repository_class(me=request.user).make_review_to_self_employed_by_admin_or_manager(
                user_id=kwargs.get('user_id'),
                text=serializer.validated_data['text'],
                value=serializer.validated_data['value'],
                point=point,
                shift_id=serializer.validated_data.get('shift')
            )
            return Response(None, status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        pagination = RequestMapper.pagination(request)
        queryset = self.get_request_repository_class().get_self_employed_reviews(
            user_id=kwargs.get('user_id'), pagination=pagination
        )
        return Response(camelize(DistributorReviewsSerializer(queryset, many=True).data))


class ConfirmAppealByManagerAPIView(CRUDAPIView):
    repository_class = ShiftAppealsRepository

    def post(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        status_changed, appeal = ShiftAppealsRepository(me=request.user).confirm_by_manager(
            record_id=record_id)

        _MANAGER_ACCEPTED_APPEAL_TITLE = 'Отклик одобрен'

        if status_changed:
            # Отправляем по сокетам смену status и job_status смз и менеджерам
            applier_sockets, managers_sockets, users_and_managers = self.repository_class \
                .get_self_employed_and_managers_with_sockets(appeal=appeal)

            send_socket_event_on_appeal_statuses(
                appeal=appeal, applier_sockets=applier_sockets, managers_sockets=managers_sockets
            )

            title = _MANAGER_ACCEPTED_APPEAL_TITLE
            message = f'Ваш отклик на вакансию {appeal.shift.vacancy.title} одобрен'
            action = NotificationAction.VACANCY.value
            subject_id = appeal.shift.vacancy_id
            notification_type = NotificationType.SYSTEM.value
            icon_type = NotificationIcon.VACANCY_APPROVED.value

            # uuid для массовой рассылки оповещений,
            # у пользователей в бд будут созданы оповещения с одинаковым uuid
            # uuid необходим на клиенте для фильтрации одинаковых данных, полученных по 2 каналам - сокеты и пуши
            common_uuid = uuid.uuid4()

            PushController().send_notification(
                users_to_send=[appeal.applier],
                title=title,
                message=message,
                common_uuid=common_uuid,
                action=action,
                subject_id=subject_id,
                notification_type=notification_type,
                icon_type=icon_type
            )

            # Отправка уведомления по сокетам
            SocketController(request.user, version='1.0').send_notification_to_many_connections(
                applier_sockets,
                {
                    'title': title,
                    'message': message,
                    'uuid': str(common_uuid),
                    'action': action,
                    'subjectId': subject_id,
                    'notificationType': notification_type,
                    'iconType': icon_type,
                })

        return Response(camelize(ShiftAppealsForManagersSerializer(appeal, many=False).data), status=status.HTTP_200_OK)


class RejectAppealByManagerAPIView(CRUDAPIView):
    repository_class = ShiftAppealsRepository

    def post(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        data = get_request_body(request)
        status_changed, appeal = ShiftAppealsRepository(me=request.user).reject_by_manager(
            record_id=record_id,
            reason=data.get('reason'),
            text=data.get('text')
        )

        _MANAGER_REJECTED_APPEAL_TITLE = 'Отклик отклонён'

        if status_changed:
            # Отправляем по сокетам смену status и job_status смз и менеджерам
            applier_sockets, managers_sockets, users_and_managers = self.repository_class \
                .get_self_employed_and_managers_with_sockets(appeal=appeal)

            send_socket_event_on_appeal_statuses(
                appeal=appeal, applier_sockets=applier_sockets, managers_sockets=managers_sockets
            )

            title = _MANAGER_REJECTED_APPEAL_TITLE
            message = f'Ваш отклик на вакансию {appeal.shift.vacancy.title} отклонён'
            action = NotificationAction.VACANCY.value
            subject_id = appeal.shift.vacancy_id
            notification_type = NotificationType.SYSTEM.value
            icon_type = NotificationIcon.VACANCY_DECLINED.value

            # uuid для массовой рассылки оповещений,
            # у пользователей в бд будут созданы оповещения с одинаковым uuid
            # uuid необходим на клиенте для фильтрации одинаковых данных, полученных по 2 каналам - сокеты и пуши
            common_uuid = uuid.uuid4()

            PushController().send_notification(
                users_to_send=[appeal.applier],
                title=title,
                message=message,
                common_uuid=common_uuid,
                action=action,
                subject_id=subject_id,
                notification_type=notification_type,
                icon_type=icon_type
            )

            # Отправка уведомления по сокетам
            SocketController(request.user, version='1.0').send_notification_to_many_connections(
                applier_sockets,
                {
                    'title': title,
                    'message': message,
                    'uuid': str(common_uuid),
                    'action': action,
                    'subjectId': subject_id,
                    'notificationType': notification_type,
                    'iconType': icon_type,
                })

        return Response(camelize(ShiftAppealsForManagersSerializer(appeal, many=False).data), status=status.HTTP_200_OK)


class ToggleLikeVacancy(APIView):
    repository = VacanciesRepository

    def post(self, request, **kwargs):
        vacancy = self.repository(me=request.user).get_by_id(kwargs['record_id'])
        self.repository(me=request.user).toggle_like(vacancy=vacancy)
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class Professions(CRUDAPIView):
    serializer_class = ProfessionSerializer
    repository_class = ProfessionsRepository
    allowed_http_methods = ['get']

    filter_params = {
        'name': 'name__istartswith',
    }

    default_order_params = []

    default_filters = {
        'is_suggested': False,
    }

    order_params = {
        'name': 'name',
        'id': 'id'
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


@api_view(['POST'])
def suggest_profession(request):
    body = get_request_body(request)
    name = body.get('name', None)
    if name:
        dataset = ProfessionsRepository().filter_by_kwargs(
            kwargs={
                'name__icontains': name
            }
        )
        if not dataset:
            ProfessionsRepository().add_suggested_profession(name)

    return Response(None, status=status.HTTP_204_NO_CONTENT)


class Skills(CRUDAPIView):
    serializer_class = SkillSerializer
    repository_class = SkillsRepository
    allowed_http_methods = ['get']

    filter_params = {
        'name': 'name__istartswith',
    }

    default_order_params = []

    default_filters = {
        'is_suggested': False,
    }

    order_params = {
        'name': 'name',
        'id': 'id'
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, paginator=pagination, order_by=order_params
            )
            self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class GetDocumentsForShift(CRUDAPIView):
    repository_class = ShiftsRepository

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        shift = self.repository_class().get_by_id(record_id)
        active_date = underscoreize(request.query_params).get('active_date')
        if active_date is None:
            raise HttpException(status_code=RESTErrors.BAD_REQUEST.value, detail='Необходимо передать active_date')
        conditions = MarketDocumentsRepository(me=request.user).get_conditions_for_user_on_shift(shift, active_date)
        return Response(camelize(ShiftConditionsSerializer(conditions, many=False).data), status=status.HTTP_200_OK)


class MarketDocuments(CRUDAPIView):
    allowed_http_methods = ['post']
    repository_class = MarketDocumentsRepository

    def post(self, request, *args, **kwargs):
        body = get_request_body(request)

        self.repository_class(me=request.user).accept_market_documents(
            global_docs=body.get('global'),
            distributor_id=body.get('distributor'),
            partner_id=body.get('partner'),
            vacancy_id=body.get('vacancy'),
            document_uuid=body.get('uuid'),
        )
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class ShiftForManagers(CRUDAPIView):
    allowed_http_methods = ['get']
    repository_class = ShiftsRepository

    def get(self, request, *args, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        active_date = underscoreize(request.query_params).get('active_date')
        active_date = timestamp_to_datetime(
            int(active_date)) if active_date is not None else now()  # По умолчанию текущий день

        shift = self.repository_class(me=request.user, calendar_from=active_date).get_shift_for_managers(
            record_id, active_date=active_date
        )
        return Response(camelize(ShiftForManagersSerializer(shift, many=False).data), status=status.HTTP_200_OK)


class ShiftAppealsForManagers(CRUDAPIView):
    allowed_http_methods = ['get']
    repository_class = ShiftAppealsRepository
    array_filter_params = {
        'status': 'status__in'
    }

    default_filters = {
        'status__in': [ShiftAppealStatus.INITIAL.value, ShiftAppealStatus.CONFIRMED.value]
    }

    def get(self, request, *args, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        active_date = underscoreize(request.query_params).get('active_date')
        filters = RequestMapper(self).filters(request) or dict()

        appeals = self.repository_class(me=request.user).get_shift_appeals_for_managers(
            record_id, active_date=active_date, filters=filters)
        return Response(camelize(ShiftAppealsForManagersSerializer(appeals, many=True).data), status=status.HTTP_200_OK)


class ConfirmedWorkers(CRUDAPIView):
    allowed_http_methods = ['get']
    repository_class = ShiftAppealsRepository
    serializer_class = ConfirmedWorkersShiftsSerializer
    order_params = {
        'time_start': 'shift__time_start'
    }
    array_filter_params = {
        'vacancy': 'shift__vacancy_id__in',
        'profession': 'shift__vacancy__profession_id__in',
    }

    default_filters = {
    }

    def get(self, request, *args, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        current_date = underscoreize(request.query_params).get('current_date')
        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            dataset = self.repository_class(me=request.user).get_confirmed_workers_for_manager(
                current_date=current_date, pagination=pagination, order_by=order_params, filters=filters
            )

            self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class ConfirmedWorkersProfessions(CRUDAPIView):
    allowed_http_methods = ['get']
    repository_class = ShiftAppealsRepository
    serializer_class = ConfirmedWorkerProfessionsSerializer
    order_params = {
        'id': 'shift__vacancy__profession_id',
        'title': 'shift__vacancy__profession__name'
    }

    def get(self, request, *args, **kwargs):
        current_date = underscoreize(request.query_params).get('current_date')
        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        dataset = self.repository_class(me=request.user).get_confirmed_workers_professions_for_manager(
            current_date=current_date, pagination=pagination, order_by=order_params, filters=filters
        )

        self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class ConfirmedWorkersDates(CRUDAPIView):
    allowed_http_methods = ['get']
    repository_class = ShiftAppealsRepository
    serializer_class = ConfirmedWorkerDatesSerializer

    def get(self, request, *args, **kwargs):
        calendar_from, calendar_to = RequestMapper().calendar_range(request)

        dataset = self.repository_class(me=request.user).get_confirmed_workers_dates_for_manager(
            calendar_from=calendar_from, calendar_to=calendar_to
        )

        self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        only_dates = {
            'active_dates': [{
                'timestamp': d['real_time_start'],
                'utc_offset': d['utc_offset'],
            } for d in serialized.data]
        }

        return Response(camelize(only_dates), status=status.HTTP_200_OK)


class PushSettingsForConfirmedWorkers(APIView):
    def put(self, request, **kwargs):
        validator = ConfirmedWorkerSettingsValidator(data=get_request_body(request))
        if validator.is_valid(raise_exception=True):
            appeal = ShiftAppealsRepository().get_by_id(kwargs.get('record_id'))
            ShiftAppealsRepository(me=request.user).is_related_manager(appeal)
            appeal.notify_leaving = validator.validated_data.get('notify_leaving')
            appeal.save()
            serialized = ConfirmedWorkersShiftsSerializer(appeal, many=False, context={
                'me': request.user,
                'headers': get_request_headers(request),
            })

            return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class QRView(APIView):
    def get(self, request, *args, **kwargs):
        job_status, qr_text, qr_pass, leave_time, appeal = ShiftAppealsRepository(
            me=request.user).handle_qr_related_data()
        if qr_pass is not None:
            qr_pass.update(ConfirmedWorkerSerializer(instance=request.user).data)
        data = {
            "job_status": job_status,
            "qr_text": qr_text,
            "pass": qr_pass,
            "leave_time": leave_time,
            "appeal": ShiftAppealsSerializer(instance=appeal).data if appeal else None
        }
        return Response(camelize(data))


class CheckPassByManagerAPIView(APIView):
    repository_class = ShiftAppealsRepository
    serializer_class = QRCodeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            appeal = self.repository_class().get_by_qr_text(qr_text=serializer.validated_data.get('qr_text'))
            data = self.repository_class(me=request.user).handle_pass_data_for_manager(
                qr_text=serializer.validated_data.get('qr_text')
            )
            data.update(ConfirmedWorkerSerializer(instance=appeal.applier).data)
            return Response(camelize(data))


class CheckPassBySecurityAPIView(APIView):
    repository_class = ShiftAppealsRepository
    serializer_class = QRCodeSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            appeal = self.repository_class().get_by_qr_text(qr_text=serializer.validated_data.get('qr_text'))
            data = self.repository_class(me=request.user).handle_pass_data_for_security(
                qr_text=serializer.validated_data.get('qr_text')
            )
            data.update(ConfirmedWorkerSerializer(instance=appeal.applier).data)
            return Response(camelize(data))


class RefusePassBySecurityAPIView(APIView):
    repository_class = ShiftAppealsRepository
    serializer_class = SecurityPassRefuseReasonSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            appeal = self.repository_class(me=request.user).refuse_pass_by_security(
                record_id=kwargs.get('record_id'),
                validated_data=serializer.validated_data
            )
            managers, sockets = VacanciesRepository.get_managers_and_sockets_for_vacancy(appeal.shift.vacancy)

            # Отправляем по сокетам смену status и job_status смз и менеджерам
            send_socket_event_on_appeal_statuses(
                appeal=appeal,
                applier_sockets=list(appeal.applier.sockets.all().values_list('socket_id', flat=True)) or [],
                managers_sockets=sockets
            )

            _SECURITY_REFUSED_APPEAL_TITLE = 'Охрана не пропустила работника'

            title = _SECURITY_REFUSED_APPEAL_TITLE
            message = f'Сотрудники охраны не пропустили работника {request.user.first_name} {request.user.last_name} по вакансии {appeal.shift.vacancy.title}'
            action = NotificationAction.VACANCY.value
            subject_id = appeal.shift.vacancy_id
            notification_type = NotificationType.SYSTEM.value
            icon_type = NotificationIcon.SECURITY_CANCELLATION_REASON.value

            # uuid для массовой рассылки оповещений,
            # у пользователей в бд будут созданы оповещения с одинаковым uuid
            # uuid необходим на клиенте для фильтрации одинаковых данных, полученных по 2 каналам - сокеты и пуши
            common_uuid = uuid.uuid4()

            PushController().send_notification(
                users_to_send=managers,
                title=title,
                message=message,
                common_uuid=common_uuid,
                action=action,
                subject_id=subject_id,
                notification_type=notification_type,
                icon_type=icon_type
            )

            # Отправка уведомления по сокетам
            SocketController(request.user, version='1.0').send_notification_to_many_connections(sockets, {
                'title': title,
                'message': message,
                'uuid': str(common_uuid),
                'action': action,
                'subjectId': subject_id,
                'notificationType': notification_type,
                'iconType': icon_type,
            })

            return Response(None, status=status.HTTP_204_NO_CONTENT)


class AllowPassByManagerAPIView(APIView):
    repository_class = ShiftAppealsRepository

    def post(self, request, *args, **kwargs):
        appeal = self.repository_class(me=request.user).allow_pass_by_manager(
            record_id=kwargs.get('record_id'))

        # Отправляем по сокетам смену status и job_status смз и менеджерам
        applier_sockets, managers_sockets, users_and_managers = self.repository_class \
            .get_self_employed_and_managers_with_sockets(appeal=appeal)

        send_socket_event_on_appeal_statuses(
            appeal=appeal, applier_sockets=applier_sockets, managers_sockets=managers_sockets
        )

        return Response(None, status=status.HTTP_204_NO_CONTENT)


class RefusePassByManagerAPIView(APIView):
    repository_class = ShiftAppealsRepository
    serializer_class = ManagerAppealCancelReasonSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            appeal = self.repository_class(me=request.user).refuse_pass_by_manager(
                record_id=kwargs.get('record_id'),
                validated_data=serializer.validated_data
            )

            # Отправляем по сокетам смену status и job_status смз и менеджерам
            applier_sockets, managers_sockets, users_and_managers = self.repository_class \
                .get_self_employed_and_managers_with_sockets(appeal=appeal)

            send_socket_event_on_appeal_statuses(
                appeal=appeal, applier_sockets=applier_sockets, managers_sockets=managers_sockets
            )

            return Response(None, status=status.HTTP_204_NO_CONTENT)


class ShiftAppealCompleteByManager(APIView):
    repository_class = ShiftAppealsRepository

    serializer_class = QRCodeCompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            appeal = self.repository_class(me=request.user).complete_appeal_by_manager(
                **serializer.validated_data
            )

            # Отправляем по сокетам смену status и job_status смз и менеджерам
            applier_sockets, managers_sockets, users_and_managers = self.repository_class \
                .get_self_employed_and_managers_with_sockets(appeal=appeal)

            send_socket_event_on_appeal_statuses(
                appeal=appeal, applier_sockets=applier_sockets, managers_sockets=managers_sockets
            )

            return Response(None, status=status.HTTP_204_NO_CONTENT)


class FireByManagerAPIView(APIView):
    repository_class = ShiftAppealsRepository
    serializer_class = FireByManagerReasonSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            self.repository_class(me=request.user).fire_by_manager(
                record_id=kwargs.get('record_id'),
                validated_data=serializer.validated_data
            )
            return Response(None, status=status.HTTP_204_NO_CONTENT)


class CancelFiringByManager(APIView):
    repository_class = ShiftAppealsRepository

    def post(self, request, *args, **kwargs):
        self.repository_class(me=request.user).cancel_firing_by_manager(
            record_id=kwargs.get('record_id'),
        )
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class ProlongByManager(APIView):
    repository_class = ShiftAppealsRepository
    serializer_class = ProlongByManagerReasonSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            appeal = self.repository_class(me=request.user).prolong_by_manager(
                record_id=kwargs.get('record_id'),
                validated_data=serializer.validated_data
            )
            # Отправляем по сокетам смену status и job_status смз и менеджерам
            applier_sockets, managers_sockets, users_and_managers = self.repository_class \
                .get_self_employed_and_managers_with_sockets(appeal=appeal)

            send_socket_event_on_appeal_statuses(
                appeal=appeal, applier_sockets=applier_sockets, managers_sockets=managers_sockets
            )
            return Response(None, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def work_location(request, **kwargs):
    body = get_request_body(request)
    point, screen_diagonal_points, radius = RequestMapper().geo(request)

    if not body.get('shift'):
        raise HttpException(status_code=RESTErrors.BAD_REQUEST.value, detail='Необходимо передать номер смены')

    should_notify_managers, managers, sockets, chat_id = ShiftsRepository(
        me=request.user
    ).work_location_update(
        point=point,
        shift_id=body.get('shift')
    )

    _WORKER_LEFT_SHOP_AREA_TITLE = 'Покидание территории магазина во время смены'
    if should_notify_managers:
        title = _WORKER_LEFT_SHOP_AREA_TITLE
        message = f'Работник {request.user.first_name} {request.user.last_name} удалился на большое расстояние'
        action = NotificationAction.CHAT.value
        subject_id = chat_id
        notification_type = NotificationType.SYSTEM.value
        icon_type = NotificationIcon.LEFT_SHOP_AREA.value

        # uuid для массовой рассылки оповещений,
        # у пользователей в бд будут созданы оповещения с одинаковым uuid
        # uuid необходим на клиенте для фильтрации одинаковых данных, полученных по 2 каналам - сокеты и пуши
        common_uuid = uuid.uuid4()

        PushController().send_notification(
            users_to_send=managers,
            title=title,
            message=message,
            common_uuid=common_uuid,
            action=action,
            subject_id=subject_id,
            notification_type=notification_type,
            icon_type=icon_type
        )

        # Отправка уведомления по сокетам
        SocketController(version='1.0').send_notification_to_many_connections(sockets, {
            'title': title,
            'message': message,
            'uuid': str(common_uuid),
            'action': action,
            'subjectId': subject_id,
            'notificationType': notification_type,
            'iconType': icon_type,
        })

    return Response(None, status=status.HTTP_204_NO_CONTENT)


class Partners(CRUDAPIView):
    serializer_class = PartnersSerializer
    repository_class = PartnersRepository
    allowed_http_methods = ['get']

    filter_params = {
        'search': 'distributor__title__istartswith',
    }

    array_filter_params = {
        'category': 'distributor__categories__id__in',
    }

    order_params = {
        'id': 'id',
        'title': 'title',
    }

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class().inited_get_by_id(record_id)
        else:
            dataset = self.repository_class().inited_filter_by_kwargs(
                kwargs=filters, order_by=order_params, paginator=pagination
            )

            self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class PartnersCategories(CRUDAPIView):
    serializer_class = CategoriesSerializer
    repository_class = PartnersRepository
    allowed_http_methods = ['get']

    filter_params = {
        'search': 'distributorcategory__distributor__title__istartswith',
    }

    order_params = {
        'id': 'id',
    }

    default_order_params = ['id']

    def get(self, request, **kwargs):
        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        dataset = self.repository_class().get_all_categories(
            kwargs=filters, order_by=order_params, paginator=pagination
        )

        serialized = self.serializer_class(dataset, many=True, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class GetDocumentsForPartner(CRUDAPIView):
    repository_class = PartnersRepository

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        partner = self.repository_class().inited_get_by_id(record_id)
        conditions = MarketDocumentsRepository(me=request.user).get_conditions_for_user_on_partner(partner)
        return Response(camelize(PartnerConditionsSerializer(conditions, many=False).data), status=status.HTTP_200_OK)


class Achievements(CRUDAPIView):
    serializer_class = AchievementsSerializer
    repository_class = AchievementsRepository
    allowed_http_methods = ['get']

    date_filter_params = {
        'completed_at': 'completed_at'
    }

    bool_filter_params = {
        'completed': 'completed'
    }

    order_params = {
        'id': 'id',
        'title': 'title',
        'completed_at': 'completed_at'
    }

    default_order_params = [
        '-completed_at'
    ]

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class(me=request.user).inited_get_by_id(record_id)
        else:
            dataset = self.repository_class(me=request.user).inited_filter_by_kwargs(
                kwargs=filters, order_by=order_params, paginator=pagination
            )

            self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Advertisements(CRUDAPIView):
    serializer_class = AdvertisementsSerializer
    repository_class = AdvertisementsRepository
    allowed_http_methods = ['get']

    order_params = {
        'id': 'id',
        'title': 'title',
        'created_at': 'created_at'
    }

    default_order_params = [
        '-created_at'
    ]

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, order_by=order_params, paginator=pagination
            )

            self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Orders(CRUDAPIView):
    serializer_class = OrdersSerializer
    repository_class = OrdersRepository
    allowed_http_methods = ['get']

    order_params = {
        'id': 'id',
        'title': 'title',
        'created_at': 'created_at'
    }

    default_order_params = [
        '-created_at'
    ]

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            dataset = self.repository_class().filter_by_kwargs(
                kwargs=filters, order_by=order_params, paginator=pagination
            )

            self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        body = get_request_body(request)
        dataset = self.repository_class(me=request.user).place_order(body)

        self.many = False

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Coupons(CRUDAPIView):
    serializer_class = CouponsSerializer
    repository_class = CouponsRepository
    allowed_http_methods = ['get']

    filter_params = {
        'search': 'partner__distributor__title__istartswith',
    }

    array_filter_params = {
        'category': 'partner__distributor__categories__id__in',
    }

    order_params = {
        'id': 'id',
        'created_at': 'created_at'
    }

    default_order_params = [
        '-created_at'
    ]

    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        if record_id:
            dataset = self.repository_class().get_by_id(record_id)
        else:
            dataset = self.repository_class(me=request.user).inited_filter_by_kwargs(
                kwargs=filters, order_by=order_params, paginator=pagination
            )

            self.many = True

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })
        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class Finances(CRUDAPIView):
    serializer_class = FinancesSerializer
    repository_class = TransactionsRepository
    allowed_http_methods = ['get']

    order_params = {
        'date': 'date'
    }

    def get(self, request, **kwargs):
        pagination = RequestMapper.pagination(request)
        point, *_ = RequestMapper().geo(request)  # *_  - все ненужные распакованные переменные

        validator = FinancesValiadator(data=request.query_params)
        if validator.is_valid(raise_exception=True):
            dataset = self.repository_class(me=request.user).get_grouped_stats(
                interval=validator.validated_data.get('interval'),
                currency=validator.validated_data.get('currency'),
                paginator=pagination,
                timezone_name=get_timezone_name_by_geo(point.x, point.y) if point else 'UTC'
            )

            self.many = True

            serialized = self.serializer_class(dataset, many=self.many, context={
                'me': request.user,
                'headers': get_request_headers(request),
            })
            return Response(camelize(serialized.data), status=status.HTTP_200_OK)


@api_view(['GET'])
def get_my_money(request):
    money_balances = MoneyRepository(me=request.user).get_my_money()
    serializer = MoneySerializer(money_balances, many=True, context={'me': request.user})
    return Response(camelize(serializer.data), status=status.HTTP_200_OK)
