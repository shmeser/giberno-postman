from app_geo.models import Language
from app_geo.versions.v1_0.repositories import LanguagesRepository
from backend.mixins import CRUDSerializer


class LanguageSerializer(CRUDSerializer):
    repository = LanguagesRepository

    class Meta:
        model = Language
        fields = [
            'id',
            'iso_code',
            'name',
            'native',
        ]

        extra_kwargs = {
            'iso_code': {'read_only': True},
            'name': {'read_only': True},
            'native': {'read_only': True}
        }
