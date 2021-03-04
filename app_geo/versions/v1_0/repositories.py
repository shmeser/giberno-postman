from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models import GeometryField, FilteredRelation, Q, Exists, OuterRef
from django.contrib.gis.db.models.functions import Distance, BoundingCircle
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Prefetch, F, ExpressionWrapper

from app_geo.models import Language, Country, City, Region
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.mixins import MasterRepository
from giberno.settings import NEAREST_POINT_DISTANCE_MAX


class LanguagesRepository(MasterRepository):
    model = Language

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )


class CountriesRepository(MasterRepository):
    model = Country

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    @staticmethod
    def fast_related_loading(queryset):
        country_ct = ContentType.objects.get_for_model(Country).id
        queryset = queryset.prefetch_related(
            Prefetch(
                'media',
                queryset=MediaModel.objects.filter(
                    owner_ct_id=country_ct,
                    type=MediaType.FLAG.value,
                    format=MediaFormat.IMAGE.value,
                ).order_by('-created_at'),
                to_attr='medias'  # Подгружаем флаги в поле medias
            )
        )

        return queryset


class RegionsRepository(MasterRepository):
    model = Region

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )


class CitiesRepository(MasterRepository):
    model = City

    def __init__(self, point=None, screen_diagonal_points=None, me=None) -> None:
        super().__init__()

        self.me = me
        self.point = point
        self.screen_diagonal_points = screen_diagonal_points

        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects

        # Фильтрация по вхождению в область на карте
        if self.screen_diagonal_points:
            self.base_query = self.base_query.filter(
                position__contained=ExpressionWrapper(
                    BoundingCircle(screen_diagonal_points),
                    output_field=GeometryField()
                )
            )

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        try:
            if order_by:
                records = self.base_query.order_by(*order_by).exclude(deleted=True).filter(**kwargs)
            else:
                records = self.base_query.exclude(deleted=True).filter(**kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.base_query.order_by(*order_by).filter(**kwargs)
            else:
                records = self.base_query.filter(**kwargs)

        return self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[paginator.offset:paginator.limit] if paginator else records,
            point=self.point
        )

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    def geocode(self, point):
        # Если входит в территорию нескольких зон, то сортируем по убыванию численности населения - нулы в конце
        within_boundary = self.model.objects.filter(boundary__covers=point).order_by(
            F('population').desc(nulls_last=True)
        )
        if not within_boundary:
            # Если не входит в зоны, то ищем ближайшие точки до которых менее NEAREST_POINT_DISTANCE_MAX метров
            # Сортировка по возрастанию удаленности
            near_point = self.model.objects.annotate(distance=Distance('position', point)).filter(
                distance__lte=NEAREST_POINT_DISTANCE_MAX).order_by('distance')
            return near_point
        return within_boundary

    def map(self, kwargs, paginator=None, order_by: list = None):
        queryset = self.filter_by_kwargs(kwargs, paginator, order_by)

        return self.clustering(queryset)

    def clustering(self, queryset):
        raw_sql = f'''
            SELECT
                c.id,
                cl.geometries_count,
                cl.centroid,
                c.native
            FROM 
                (
                    SELECT 
                        cluster_geometries,
                        ST_Centroid (cluster_geometries) AS centroid,
                        ST_NumGeometries(cluster_geometries) as geometries_count,
                        ST_ClosestPoint(
                            cluster_geometries, 
                            ST_GeomFromGeoJSON('{self.point.geojson}')
                        ) AS closest_point
                    FROM 
                        UNNEST(
                            (
                                SELECT 
                                    ST_ClusterWithin(position,5000/111111.0) 
                                FROM 
                                    (
                                    {queryset.only('position', 'country', 'region').query}
                                    ) subquery
                            )
                        ) cluster_geometries
                ) cl
            JOIN app_geo__cities c ON (c.position=cl.closest_point) -- JOIN с ближайшей точкой 

            ORDER BY 2 DESC
        '''
        return self.model.objects.raw(raw_sql)

    @staticmethod
    def fast_related_loading(queryset, point=None):
        queryset = queryset.select_related('country', 'region')
        return queryset

    def get_suggestions(self, search, paginator=None):
        records = self.model.objects.exclude(deleted=True).annotate(
            similarity=TrigramSimilarity('native', search),
        ).filter(native__trigram_similar=search).order_by('-similarity')

        records = records.only('native').distinct().values_list('native', flat=True)
        return records[paginator.offset:paginator.limit] if paginator else records[:100]
