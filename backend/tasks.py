import mimetypes
import sys
from tempfile import NamedTemporaryFile

from cairosvg import svg2png
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import UploadedFile
from django.utils.timezone import now

from app_geo.models import Country
from app_geo.versions.v1_0.repositories import CountriesRepository
from app_media.enums import FileDownloadStatus, MediaType, MimeTypes
from app_media.mappers import MediaMapper
from app_media.versions.v1_0.repositories import MediaRepository
from backend.utils import get_remote_file
from giberno.celery import app
from giberno.settings import IMAGE_PREVIEW_SIDE_MAX


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
        'owner_content_type_id': country_ct.id,
        'type': MediaType.FLAG
    }).update(deleted=True, updated_at=now())

    for country in countries:
        flag_url = country.osm.get('flag', None)
        try:
            dl_file, content_type, size, status = get_remote_file(flag_url)

            if status == FileDownloadStatus.SAVED:
                suffix = mimetypes.guess_extension(content_type)
                temp_file = NamedTemporaryFile(delete=True, suffix=suffix)
                temp_file.write(dl_file)
                temp_file.flush()

                uploaded = UploadedFile(file=temp_file, size=size, content_type=content_type)

                mapped_file = MediaMapper.combine(
                    uploaded, country, file_type=MediaType.FLAG, file_title=country.names.get('name:en', None)
                )
                if mapped_file:
                    mapped_entities.append(mapped_file)

        except Exception as e:
            print(e)

    if mapped_entities:
        MediaRepository().bulk_create(mapped_entities)


@app.task
def countries_update_flag_png(countries_ids: list = None):
    mapped_entities = []

    # Удаляем старые флаги
    country_ct = ContentType.objects.get_for_model(Country)
    MediaRepository().filter_by_kwargs({
        'deleted': False,
        'owner_id__in': countries_ids,
        'owner_content_type_id': country_ct.id,
        'mime_type': MimeTypes.PNG.value,
        'type': MediaType.FLAG
    }).update(deleted=True, updated_at=now())

    media_files = MediaRepository().filter_by_kwargs({
        'deleted': False,
        'owner_id__in': countries_ids,
        'owner_content_type_id': country_ct.id,
        'mime_type': MimeTypes.SVG.value,
        'type': MediaType.FLAG
    })

    for file in media_files:
        try:
            country = Country.objects.get(pk=file.owner_id)

            png = svg2png(file_obj=file.file, output_height=IMAGE_PREVIEW_SIDE_MAX, output_width=IMAGE_PREVIEW_SIDE_MAX)

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
            print(e)

    if mapped_entities:
        MediaRepository().bulk_create(mapped_entities)
