from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db.models.functions import Distance, Envelope
from django.contrib.gis.geos import MultiPoint
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Prefetch, F, ExpressionWrapper

from app_geo.models import Language, Country, City, Region
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from backend.errors.enums import RESTErrors
from backend.errors.http_exceptions import HttpException
from backend.mixins import MasterRepository
from giberno import settings
from giberno.settings import NEAREST_POINT_DISTANCE_MAX, CLUSTER_MIN_POINTS_COUNT, CLUSTER_NESTED_ITEMS_COUNT


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
                    deleted=False,
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
                    Envelope(  # BoundingCircle использовался для описывающего круга
                        MultiPoint(
                            self.screen_diagonal_points[0], self.screen_diagonal_points[1], srid=settings.SRID
                        )
                    ),
                    output_field=GeometryField()
                )
            )

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None, prefetch=True):
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

        if prefetch:
            return self.fast_related_loading(  # Предзагрузка связанных сущностей
                queryset=records[paginator.offset:paginator.limit] if paginator else records,
                point=self.point
            )
        else:
            return records[paginator.offset:paginator.limit] if paginator else records

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
            # Если не входит в зоны, то ищем ближайшие точки, до которых менее NEAREST_POINT_DISTANCE_MAX метров
            # Сортировка по возрастанию удаленности
            near_point = self.model.objects.annotate(distance=Distance('position', point)).filter(
                distance__lte=NEAREST_POINT_DISTANCE_MAX).order_by('distance')
            return near_point
        return within_boundary

    def map(self, kwargs, paginator=None, order_by: list = None):
        queryset = self.filter_by_kwargs(kwargs, paginator, order_by, prefetch=False)

        return self.clustering(queryset)

    def clustering(self, queryset):
        """
        :param queryset: Отфильтрованные по области на экране данные
        :return:
        """
        raw_sql = f'''
            WITH clusters AS (
                SELECT 
                    cid, 
                    ST_Collect(position) AS cluster_geometries, 
                    ST_Centroid (ST_Collect(position)) AS centroid,
                    ST_X(ST_Centroid (ST_Collect(position))) AS c_lon,
                    ST_Y(ST_Centroid (ST_Collect(position))) AS c_lat,
                    ARRAY_AGG(id) AS ids_in_cluster,
                    ST_NumGeometries(ST_Collect(position)) as clustered_count
                FROM (
                        SELECT 
                            id, 
                            ST_ClusterDBSCAN(
                                position, 
                                eps := ST_Distance(
                                    ST_GeomFromGeoJSON('{self.screen_diagonal_points[0].geojson}'),
                                    ST_GeomFromGeoJSON('{self.screen_diagonal_points[1].geojson}')
                                )/10.0, -- 1/10 диагонали
                                minpoints := {CLUSTER_MIN_POINTS_COUNT}
                            ) OVER() AS cid, 
                            position
                        FROM 
                            (
                                {queryset.query}
                            ) external_subquery
                        
                ) sq
                GROUP BY cid
            ),
            
            computed AS (
            
            SELECT 
                s.id,
                s.native,
                s.position::bytea,
                ST_DistanceSphere(s.position, ST_GeomFromGeoJSON('{self.point.geojson}')) AS distance,
                c.cid, 
                c.c_lat, 
                c.c_lon, 
                c.clustered_count 
            FROM app_geo__cities s
            JOIN clusters c ON (s.id=ANY(c.ids_in_cluster))
            
            )
            
            SELECT * FROM (
                SELECT 
                    *,
                    ROW_NUMBER() OVER (PARTITION BY cid ORDER BY distance ASC) AS n
                FROM computed
            ) a
            WHERE n<={CLUSTER_NESTED_ITEMS_COUNT}
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
