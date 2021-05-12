from djangorestframework_camel_case.util import camelize, underscoreize
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from app_feedback.versions.v1_0.repositories import ReviewsRepository
from app_feedback.versions.v1_0.serializers import POSTReviewSerializer, ReviewModelSerializer, \
    POSTReviewByManagerSerializer
from app_market.enums import AppealCancelReason
from app_market.versions.v1_0.repositories import VacanciesRepository, ProfessionsRepository, SkillsRepository, \
    DistributorsRepository, ShopsRepository, ShiftsRepository, UserShiftRepository, ShiftAppealsRepository, \
    MarketDocumentsRepository
from app_market.versions.v1_0.serializers import QRCodeSerializer, UserShiftSerializer, VacanciesClusterSerializer, \
    ShiftAppealsSerializer, VacanciesWithAppliersForManagerSerializer, ShiftAppealCreateSerializer, \
    ShiftsWithAppealsSerializer, ShiftConditionsSerializer
from app_market.versions.v1_0.serializers import VacancySerializer, ProfessionSerializer, SkillSerializer, \
    DistributorsSerializer, ShopSerializer, VacanciesSerializer, ShiftsSerializer
from app_sockets.controllers import SocketController
from app_users.permissions import IsManagerOrSecurity
from app_users.versions.v1_0.repositories import ProfileRepository
from backend.api_views import BaseAPIView
from backend.entity import Error
from backend.errors.enums import ErrorsCodes, RESTErrors
from backend.errors.http_exceptions import CustomException, HttpException
from backend.mappers import RequestMapper, DataMapper
from backend.mixins import CRUDAPIView
from backend.utils import get_request_body, chained_get, get_request_headers


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
            dataset = self.repository_class(point).get_by_id(record_id)
            dataset.increment_views_count()
        else:
            self.many = True
            dataset = self.repository_class(point, screen_diagonal_points).filter_by_kwargs(
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
        serializer = ShiftAppealCreateSerializer(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            instance = self.repository_class(me=request.user).get_or_create(**serializer.validated_data)
            return Response(camelize(ShiftAppealsSerializer(instance=instance, many=False).data))

    def put(self, request, *args, **kwargs):
        serializer = ShiftAppealCreateSerializer(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            record_id = kwargs.get(self.urlpattern_record_id_name)
            instance = self.repository_class(me=request.user).update(record_id, **serializer.validated_data)
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
        self.repository_class(me=request.user).cancel(record_id=record_id, reason=reason, text=data.get('text'))
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class ActiveVacanciesWithAppliersByDateForManagerListAPIView(CRUDAPIView):
    serializer_class = VacanciesWithAppliersForManagerSerializer
    repository_class = VacanciesRepository
    allowed_http_methods = ['get']

    filter_params = {
    }

    order_params = {
        'title': 'title',
        'created_at': 'created_at',
        'id': 'id'
    }

    def get(self, request, *args, **kwargs):
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        current_date, next_day = RequestMapper(self).current_date_range(request)

        if not current_date:
            dataset = self.repository_class(me=request.user).queryset_by_manager(order_params=order_params,
                                                                                 pagination=pagination)
        else:
            dataset = self.repository_class(me=request.user).queryset_filtered_by_current_date_range_for_manager(
                order_params=order_params, pagination=pagination, current_date=current_date, next_day=next_day
            )

        serialized = self.serializer_class(dataset, many=True, context={
            'me': request.user,
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
    serializer_class = VacancySerializer
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
    filter_params = {}
    order_params = {}

    def get(self, request, **kwargs):
        pagination = RequestMapper.pagination(request)
        current_date, next_day = RequestMapper(self).current_date_range(request)

        dataset = self.repository_class(me=request.user).vacancy_shifts_with_appeals_queryset(
            record_id=kwargs.get('record_id'),
            pagination=pagination,
            current_date=current_date,
            next_day=next_day
        )

        serialized = self.serializer_class(dataset, many=True, context={
            'me': request.user,
            'current_date': current_date,
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


class UserShiftsListAPIView(CRUDAPIView):
    serializer_class = UserShiftSerializer
    repository_class = UserShiftRepository
    allowed_http_methods = ['get']

    filter_params = {
        'status': 'status'
    }

    bool_filter_params = {

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
        filters = RequestMapper(self).filters(request) or dict()
        filters.update({'user': request.user})
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        dataset = self.repository_class().filter_by_kwargs(
            kwargs=filters, order_by=order_params, paginator=pagination
        )

        serialized = self.serializer_class(dataset, many=True, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class UserShiftsRetrieveAPIView(CRUDAPIView):
    serializer_class = UserShiftSerializer
    repository_class = UserShiftRepository
    allowed_http_methods = ['get']

    def get(self, request, **kwargs):
        user_shift = self.repository_class().get_by_id(kwargs.get('record_id'))

        serialized = self.serializer_class(user_shift, many=False, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class VacanciesStats(Vacancies):
    def get(self, request, **kwargs):
        filters = RequestMapper(self).filters(request) or dict()
        order_params = RequestMapper(self).order(request)

        point, screen_diagonal_points, radius = RequestMapper().geo(request)
        dataset = self.repository_class(point, screen_diagonal_points).filter_by_kwargs(
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
        dataset = self.repository_class(point, screen_diagonal_points).filter_by_kwargs(
            kwargs=filters, order_by=order_params
        )

        distributors = self.repository_class().aggregate_distributors(dataset, pagination)
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
        dataset = VacanciesRepository().get_suggestions(
            # trigram_similar Поиск с использованием pg_trgm на проиндексированном поле
            search=search,
            paginator=pagination
        )
    return Response(dataset, status=status.HTTP_200_OK)


@api_view(['GET'])
def similar_vacancies(request, **kwargs):
    pagination = RequestMapper.pagination(request)
    point, screen_diagonal_points, radius = RequestMapper().geo(request)
    vacancies = VacanciesRepository(point=point, screen_diagonal_points=screen_diagonal_points,
                                    me=request.user).get_similar(
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
        return Response(ReviewModelSerializer(instance=queryset, many=True).data)


class VacancyReviewsAPIView(ReviewsBaseAPIView):
    serializer_class = POSTReviewSerializer
    get_request_repository_class = ReviewsRepository
    post_request_repository_class = VacanciesRepository


class ShopReviewsAPIView(ReviewsBaseAPIView):
    serializer_class = POSTReviewSerializer
    get_request_repository_class = ReviewsRepository
    post_request_repository_class = ShopsRepository


class DistributorReviewsAPIView(ReviewsBaseAPIView):
    serializer_class = POSTReviewSerializer
    get_request_repository_class = ReviewsRepository
    post_request_repository_class = DistributorsRepository


class SelfEmployedUserReviewsByAdminOrManagerAPIView(ReviewsBaseAPIView):
    serializer_class = POSTReviewByManagerSerializer
    get_request_repository_class = ReviewsRepository
    post_request_repository_class = ProfileRepository

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        point, screen_diagonal_points, radius = RequestMapper().geo(request)

        if serializer.is_valid(raise_exception=True):
            self.post_request_repository_class(me=request.user).make_review_to_self_employed_by_admin_or_manager(
                record_id=kwargs.get('record_id'),
                text=serializer.validated_data['text'],
                value=serializer.validated_data['value'],
                point=point,
                shift=serializer.validated_data.get('shift')
            )
            return Response(None, status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        pagination = RequestMapper.pagination(request)
        kwargs = {
            'target_id': kwargs['record_id'],
            'deleted': False
        }
        queryset = self.get_request_repository_class().filter_by_kwargs(kwargs=kwargs, paginator=pagination)
        return Response(ReviewModelSerializer(instance=queryset, many=True).data)


class ConfirmAppealByManagerAPIView(CRUDAPIView):
    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        status_changed, sockets, appeal = ShiftAppealsRepository(me=request.user).confirm_by_manager(
            record_id=record_id)

        if status_changed:
            SocketController().send_message_to_many_connections(sockets, {
                'type': 'appeal_status_updated',
                'prepared_data': {
                    'id': appeal.id,
                    'status': appeal.status,
                }
            })

        return Response(None, status=status.HTTP_200_OK)


class RejectAppealByManagerAPIView(CRUDAPIView):
    def get(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        status_changed, sockets, appeal = ShiftAppealsRepository(me=request.user).reject_by_manager(record_id=record_id)

        if status_changed:
            SocketController().send_message_to_many_connections(sockets, {
                'type': 'appeal_status_updated',
                'prepared_data': {
                    'id': appeal.id,
                    'status': appeal.status,
                }
            })

        return Response(None, status=status.HTTP_200_OK)


class ToggleLikeVacancy(APIView):
    repository = VacanciesRepository

    def post(self, request, **kwargs):
        vacancy = self.repository().get_by_id(kwargs['record_id'])
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


class CheckUserShiftByManagerOrSecurityAPIView(BaseAPIView):
    permission_classes = [IsManagerOrSecurity]
    serializer_class = QRCodeSerializer
    repository_class = UserShiftRepository

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            user_shift = self.repository_class().get_by_qr_data(qr_data=serializer.validated_data.get('qr_data'))
            self.repository_class(me=request.user).update_status_by_qr_check(instance=user_shift)
            return Response(UserShiftSerializer(instance=user_shift).data, status=status.HTTP_200_OK)


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
            vacancy_id=body.get('vacancy'),
            document_uuid=body.get('uuid'),
        )
        return Response(None, status=status.HTTP_204_NO_CONTENT)
