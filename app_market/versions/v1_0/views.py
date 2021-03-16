from datetime import timedelta, datetime

from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from app_feedback.versions.v1_0.repositories import ReviewsRepository
from app_feedback.versions.v1_0.serializers import POSTReviewSerializer, ReviewModelSerializer
from app_market.enums import ShiftStatus
from app_market.models import UserShift, VacancyAppeal
from app_market.versions.v1_0.repositories import VacanciesRepository, ProfessionsRepository, SkillsRepository, \
    DistributorsRepository, ShopsRepository, ShiftsRepository, UserShiftRepository
from app_market.versions.v1_0.serializers import QRCodeSerializer, UserShiftSerializer, VacanciesClusterSerializer, \
    VacanciesListForManagerSerializer, SingleVacancyForManagerSerializer, AppliedUsersByVacancyForManagerSerializer, \
    ApplyToVacancyResponseSerializer
from app_market.versions.v1_0.serializers import VacancySerializer, ProfessionSerializer, SkillSerializer, \
    DistributorsSerializer, ShopSerializer, VacanciesSerializer, ShiftsSerializer
from app_users.permissions import IsManagerOrSecurity
from backend.api_views import BaseAPIView
from backend.errors.http_exception import HttpException
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


class ApplyToVacancyAPIView(CRUDAPIView):
    serializer_class = ApplyToVacancyResponseSerializer
    repository_class = VacanciesRepository

    def get(self, request, *args, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        vacancy = self.repository_class().get_by_id(record_id)
        appeal, created = VacancyAppeal.objects.get_or_create(user=request.user, vacancy=vacancy)
        return Response(self.serializer_class(instance=appeal).data)

    def delete(self, request, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)
        vacancy = self.repository_class().get_by_id(record_id)
        appeal, created = VacancyAppeal.objects.get_or_create(user=request.user, vacancy=vacancy)
        appeal.delete()
        return Response(None, status=status.HTTP_204_NO_CONTENT)


class GetVacanciesByManagerShopAPIView(CRUDAPIView):
    serializer_class = VacanciesListForManagerSerializer
    repository_class = VacanciesRepository
    allowed_http_methods = ['get']

    filter_params = {
        'available_from': 'available_from__gt'
    }

    order_params = {
        'title': 'title',
        'created_at': 'created_at',
        'id': 'id'
    }

    def get(self, request, *args, **kwargs):
        pagination = RequestMapper.pagination(request)
        order_params = RequestMapper(self).order(request)

        filters = RequestMapper(self).filters(request) or dict()
        filters.update({
            'shop_id__in': request.user.manager_shops.all()
        })

        available_from = filters.get('available_from__gt')
        if available_from:
            next_day = datetime.strptime(available_from, '%Y-%m-%d') + timedelta(days=1)
            filters.update({
                'available_from__lt': next_day
            })

        dataset = self.repository_class().filter_by_kwargs(
            kwargs=filters, order_by=order_params, paginator=pagination
        )

        serialized = self.serializer_class(dataset, many=True, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class GetSingleVacancyForManagerAPIView(CRUDAPIView):
    serializer_class = SingleVacancyForManagerSerializer
    repository_class = VacanciesRepository
    allowed_http_methods = ['get']

    def get(self, request, *args, **kwargs):
        record_id = kwargs.get(self.urlpattern_record_id_name)

        filters = RequestMapper(self).filters(request) or dict()
        filters.update({
            'shop_id__in': request.user.manager_shops.all()
        })

        dataset = self.repository_class().get_by_id(record_id)

        serialized = self.serializer_class(dataset, many=False, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class GetAppliedUsersByVacancyForManagerAPIView(CRUDAPIView):
    serializer_class = AppliedUsersByVacancyForManagerSerializer
    pass


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
            dataset = self.repository_class(calendar_from, calendar_to).get_by_id(record_id)
        else:
            self.many = True
            dataset = self.repository_class(calendar_from, calendar_to).filter_by_kwargs(
                kwargs=filters, order_by=order_params
            )
            dataset = dataset[pagination.offset:pagination.limit]

        serialized = self.serializer_class(dataset, many=self.many, context={
            'me': request.user,
            'headers': get_request_headers(request),
        })

        return Response(camelize(serialized.data), status=status.HTTP_200_OK)


class UserShiftsAPIView(CRUDAPIView):
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
    serializer_class = POSTReviewSerializer
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

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=get_request_body(request))
        if serializer.is_valid(raise_exception=True):
            try:
                user_shift = UserShift.objects.get(qr_code=serializer.validated_data['qr_code'])
                if request.user.is_security:
                    return Response(UserShiftSerializer(instance=user_shift).data, status=status.HTTP_200_OK)
                if request.user.is_manager:
                    if user_shift.status == ShiftStatus.INITIAL:
                        user_shift.status = ShiftStatus.STARTED
                        user_shift.save()
                        return Response(UserShiftSerializer(instance=user_shift).data, status=status.HTTP_200_OK)
                    elif user_shift.status == ShiftStatus.STARTED:
                        user_shift.status = ShiftStatus.COMPLETED
                        user_shift.qr_code = None
                        user_shift.save()
                        return Response(UserShiftSerializer(instance=user_shift).data, status=status.HTTP_200_OK)
            except UserShift.DoesNotExist:
                raise HttpException({'detail': 'User shift not found'}, status_code=400)
