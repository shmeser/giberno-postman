import gzip
import mimetypes
import sys
from tempfile import NamedTemporaryFile

from cairosvg import svg2png
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import UploadedFile
from fcm_django.models import FCMDevice
from loguru import logger

from app_geo.models import Country
from app_geo.versions.v1_0.repositories import CountriesRepository
from app_market.models import Shop
from app_market.versions.v1_0.repositories import ShopsRepository
from app_media.enums import FileDownloadStatus, MediaType, MimeTypes
from app_media.mappers import MediaMapper
from app_media.versions.v1_0.repositories import MediaRepository
from backend.utils import get_remote_file
from giberno.celery import app
from giberno.settings import GOOGLE_CLOUD_API_KEY


@app.task
def countries_update_flag(countries_ids: list = None):
    mapped_entities = []
    countries = CountriesRepository().filter_by_kwargs({
        'id__in': countries_ids
    })

    # Удаляем старые флаги
    country_ct = ContentType.objects.get_for_model(Country)
    MediaRepository().filter_by_kwargs({
        'deleted': False,
        'owner_id__in': countries_ids,
        'owner_ct_id': country_ct.id,
        'type': MediaType.FLAG
    }).delete()

    for country in countries:
        flag_url = country.osm.get('flag', None)
        try:
            dl_file, content_type, size, status = get_remote_file(flag_url)

            if status == FileDownloadStatus.SAVED:
                suffix = mimetypes.guess_extension(content_type)
                temp_file = NamedTemporaryFile(delete=True, suffix=suffix)
                if content_type == MimeTypes.SVG.value:
                    dl_file = gzip.decompress(dl_file)
                temp_file.write(dl_file)
                temp_file.flush()

                uploaded = UploadedFile(file=temp_file, size=size, content_type=content_type)

                mapped_file = MediaMapper.combine(
                    uploaded, country, file_type=MediaType.FLAG, file_title=country.names.get('name:en', None)
                )
                if mapped_file:
                    mapped_entities.append(mapped_file)

        except Exception as e:
            logger.error(e)

    if mapped_entities:
        MediaRepository().bulk_create(mapped_entities)


@app.task
def countries_add_png_flag_from_svg(countries_ids: list = None):
    mapped_entities = []

    # Удаляем старые флаги
    country_ct = ContentType.objects.get_for_model(Country)
    MediaRepository().filter_by_kwargs({
        'deleted': False,
        'owner_id__in': countries_ids,
        'owner_ct_id': country_ct.id,
        'mime_type': MimeTypes.PNG.value,
        'type': MediaType.FLAG
    }).delete()

    media_files = MediaRepository().filter_by_kwargs({
        'deleted': False,
        'owner_id__in': countries_ids,
        'owner_ct_id': country_ct.id,
        'mime_type': MimeTypes.SVG.value,
        'type': MediaType.FLAG
    })

    for file in media_files:
        try:
            country = Country.objects.get(pk=file.owner_id)

            png = svg2png(file_obj=file.file)

            suffix = mimetypes.guess_extension(MimeTypes.PNG.value)
            temp_file = NamedTemporaryFile(delete=True, suffix=suffix)
            temp_file.write(png)
            temp_file.flush()

            uploaded = UploadedFile(file=temp_file, size=sys.getsizeof(png), content_type=MimeTypes.PNG.value)

            mapped_file = MediaMapper.combine(
                uploaded, country, file_type=MediaType.FLAG, file_title=country.names.get('name:en', None)
            )
            if mapped_file:
                mapped_entities.append(mapped_file)

        except Exception as e:
            logger.error(e)

    if mapped_entities:
        MediaRepository().bulk_create(mapped_entities)


@app.task
def async_send_push(title, message, push_data=None, sound=None, devices_ids=[], **kwargs):
    badge = kwargs.pop('badge', 1)
    try:
        result = FCMDevice.objects.filter(id__in=devices_ids).send_message(
            title=title,
            body=message,
            badge=badge,
            sound=sound,
            data=push_data,
            **{
                'android_channel_id': kwargs.pop('android_channel_id', None)  # Для андроида начиная с версии 8
            }
        )
        return result  # Ответ Firebase, если нужен
    except Exception as e:
        logger.error(e)
        return None


@app.task
def shops_update_static_map(shops_ids: list = None):
    mapped_entities = []
    shops = ShopsRepository().filter_by_kwargs({
        'id__in': shops_ids
    })

    # Удаляем старые статические карты
    shop_ct = ContentType.objects.get_for_model(Shop)
    MediaRepository().filter_by_kwargs({
        'deleted': False,
        'owner_id__in': shops_ids,
        'owner_ct_id': shop_ct.id,
        'type': MediaType.MAP
    }).delete()

    for shop in shops:
        if shop.location is None:
            continue  # Пропускаем итерацию, если нет геолокации у магазина

        url = f'https://maps.googleapis.com/maps/api/staticmap' \
            f'?center={shop.location.y},{shop.location.x}' \
            f'&zoom=13' \
            f'&size=600x300' \
            f'&maptype=roadmap' \
            f'&language=ru' \
            f'&key={GOOGLE_CLOUD_API_KEY}'
        try:
            dl_file, content_type, size, status = get_remote_file(url)
            if status == FileDownloadStatus.SAVED:
                suffix = mimetypes.guess_extension(content_type)
                temp_file = NamedTemporaryFile(delete=True, suffix=suffix)
                if content_type == MimeTypes.SVG.value:
                    dl_file = gzip.decompress(dl_file)
                temp_file.write(dl_file)
                temp_file.flush()

                uploaded = UploadedFile(file=temp_file, size=size, content_type=content_type)

                mapped_file = MediaMapper.combine(
                    uploaded, shop, file_type=MediaType.MAP, file_title=shop.address
                )
                if mapped_file:
                    mapped_entities.append(mapped_file)

        except Exception as e:
            logger.error(e)

    if mapped_entities:
        MediaRepository().bulk_create(mapped_entities)
