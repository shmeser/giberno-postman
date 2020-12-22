import mimetypes
from tempfile import NamedTemporaryFile

from django.core.files.uploadedfile import UploadedFile

from app_geo.versions.v1_0.repositories import CountriesRepository
from app_media.enums import FileDownloadStatus, MediaType
from app_media.mappers import MediaMapper
from app_media.versions.v1_0.repositories import MediaRepository
from backend.utils import get_remote_file
from giberno.celery import app


@app.task
def countries_update_flag(countries_ids: list = None):
    mapped_entities = []
    countries = CountriesRepository().filter_by_kwargs({
        'id__in': countries_ids
    })
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

                mapped_file = MediaMapper.combine(uploaded, country, file_type=MediaType.FLAG)
                if mapped_file:
                    mapped_entities.append(mapped_file)

        except Exception as e:
            print(e)

    if mapped_entities:
        MediaRepository().bulk_create(mapped_entities)
