from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.utils.timezone import now

from app_media.enums import MediaType
from app_media.models import MediaModel
from backend.entity import File
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.mixins import MasterRepository
from backend.utils import chained_get


class MediaRepository(MasterRepository):
    model = MediaModel

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id, is_staff=False)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail='Объект %s с ID=%d не найден' % (self.model._meta.verbose_name, record_id)
            )

    def bulk_create(self, files: [File]):
        media_models = []
        for file in files:
            media_models.append(
                self.model(**dict(file))
            )

        return self.model.objects.bulk_create(media_models)

    @staticmethod
    def get_mime_cond(x, media_type, mime_type=None):
        if mime_type:
            # Сравниваем по media_type и mime_type
            return x.type == media_type and x.mime_type == mime_type
        else:
            # Сравниваем только по media_type
            return x.type == media_type

    @classmethod
    def get_related_media(cls, model_instance, prefetched_data, m_type, m_format=None, mime_type=None, multiple=False):
        # Берем файлы из предзагруженного через prefetch_related поля medias
        medias_list = chained_get(prefetched_data, 'medias', default=list())
        iterated = filter(  # Отфильтровываем по mime_type и берем один элемент
            lambda x: cls.get_mime_cond(x, m_type, mime_type), medias_list
        )
        if multiple:
            files = list(iterated)
        else:
            files = next(iterated, None)  # Берем 1 файл

        if isinstance(model_instance, QuerySet):  # для many=True - узнаем из сериалайзера через model_instance
            return files

        # для many=False - узнаем из сериалайзера через model_instance
        if not files:  # Если нет предзагруженных данных, делаем запрос в бд
            files = MediaModel.objects.filter(
                owner_id=prefetched_data.id, type=m_type,
                owner_ct_id=ContentType.objects.get_for_model(prefetched_data).id,
            )
            if m_format:  # Если указан формат
                files = files.filter(format=m_format)
            if mime_type:  # Если указан mime_type
                files = files.filter(mime_type=mime_type)
            files = files.order_by('-created_at')
            if not multiple:
                files = files.first()

        return files

    def reattach_files(self, uuids: [str], current_model, current_owner_id, target_model, target_owner_id):
        """ Найти файлы с типом ATTACHMENT и установить нового владельца"""

        current_ct = ContentType.objects.get_for_model(current_model)
        target_ct = ContentType.objects.get_for_model(target_model)

        self.model.objects.filter(
            uuid__in=uuids,
            owner_ct=current_ct,
            owner_id=current_owner_id,
            type=MediaType.ATTACHMENT.value  # Только с типом "прикрепленные файлы"
        ).update(
            owner_ct=target_ct,
            owner_ct_name=target_ct.model,
            owner_id=target_owner_id,
            updated_at=now()
        )
