from tempfile import NamedTemporaryFile

from app_geo.versions.v1_0.repositories import CountriesRepository
from app_media.enums import FileDownloadStatus
from app_media.mappers import MediaMapper
from app_media.versions.v1_0.repositories import MediaRepository
from backend.utils import get_remote_file
from giberno.celery import app


@app.task
def countries_update_flag(countries_ids: list = None):
    mapped_entities = []
    if countries_ids:
        countries = CountriesRepository().filter_by_kwargs({
            'id__in': countries_ids
        })
        for country in countries:
            flag_url = country.osm.get('flag', None)
            if flag_url:
                try:
                    dl_file, status = get_remote_file(flag_url)

                    if status == FileDownloadStatus.SAVED:
                        temp_file = NamedTemporaryFile(delete=True)
                        temp_file.write(dl_file)
                        temp_file.flush()

                        mapped_file = MediaMapper.combine(temp_file, country)
                        if mapped_file:
                            mapped_entities.append(mapped_file)

                except Exception as e:
                    print(e)

    if mapped_entities:
        MediaRepository().bulk_create(mapped_entities)
