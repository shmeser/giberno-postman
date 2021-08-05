from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet, Q
from django.utils.timezone import now

from app_media.enums import MediaType
from app_media.models import MediaModel
from app_users.models import UserProfile
from backend.entity import File
from backend.errors.enums import RESTErrors
from backend.errors.http_exceptions import HttpException
from backend.mixins import MasterRepository
from backend.utils import chained_get


class MediaRepository(MasterRepository):
    model = MediaModel

    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id, is_staff=False)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail='Объект %s с ID=%d не найден' % (self.model._meta.verbose_name, record_id)
            )

    def remove_all_avatars(self):
        self.model.objects.filter(
            type=MediaType.AVATAR.value,
            owner_ct=ContentType.objects.get_for_model(self.me),
            owner_id=self.me.id
        ).delete()

    def bulk_create(self, files: [File]):
        media_models = []
        avatar = None  # Аватарка должна быть одна, поэтому из всех переданных аватарок выбираем последнюю
        for file in files:
            if file.type == MediaType.AVATAR.value:
                avatar = file
            else:
                media_models.append(
                    self.model(**dict(file))
                )
        if avatar and self.me:
            # Если пришла аватарка, то удаляем все старые аватарки у пользователя
            self.remove_all_avatars()
            # Добавляем аватарку в массив файлов
            media_models.append(
                self.model(**dict(avatar))
            )

        return self.model.objects.bulk_create(media_models)

    @staticmethod
    def get_mime_cond(x, media_types, mime_type=None):
        if media_types and mime_type:
            # Сравниваем по media_types и mime_type
            return x.type in media_types and x.mime_type == mime_type
        if media_types and not mime_type:
            # Сравниваем только по media_types
            return x.type in media_types

        if not media_types and mime_type:
            # Сравниваем только по mime_type
            return x.mime_type == mime_type

        return True  # В остальных случаях

    @classmethod
    def get_related_media(cls, model_instance, prefetched_data, m_types, m_format=None, mime_type=None, multiple=False,
                          only_prefetched=False):
        """
        :param model_instance:
        :param prefetched_data: Данные модели с предзагруженными связями
        :param m_types:  Типы медиа файла
        :param m_format: Формат (Изображение, документ, видео и т.д.)
        :param mime_type: MimeType
        :param multiple: Выдать несколько файлов
        :param only_prefetched:  Использовать только из предзагруженных данных
        :return:
        """

        if m_types and m_types is not list:
            m_types = [m_types]

        # Берем файлы из предзагруженного через prefetch_related поля medias
        medias_list = chained_get(prefetched_data, 'medias', default=list())
        iterated = filter(  # Отфильтровываем по mime_type и берем один элемент
            lambda x: cls.get_mime_cond(x, m_types, mime_type), medias_list
        )
        if multiple:
            files = list(iterated)
        else:
            files = next(iterated, None)  # Берем 1 файл

        if isinstance(model_instance, QuerySet):  # для many=True - узнаем из сериалайзера через model_instance
            return files

        # для many=False - узнаем из сериалайзера через model_instance
        # Если нет предзагруженных данных и нет флага "использовать из prefetch", делаем запрос в бд
        if not files and not only_prefetched:
            files = MediaModel.objects.filter(
                deleted=False,
                owner_id=prefetched_data.id,
                owner_ct_id=ContentType.objects.get_for_model(prefetched_data).id,
            )
            if m_types:
                files = files.filter(type__in=m_types)
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

    def delete_my_media(self, uuid_list, content_type_id, my_content_ids):
        """
        :param uuid_list:
        :param content_type_id: content_type зависимой от меня сущности (документ, комментарий, отзыв и т.д.)
        :param my_content_ids: ид принадлежащих мне сущностей для указанного content_type
        :return:
        """

        user_ct = ContentType.objects.get_for_model(UserProfile)
        if my_content_ids:
            query = Q(
                Q(
                    owner_ct_id=user_ct,
                    owner_id=self.me.id,
                    uuid__in=uuid_list
                ) |
                Q(
                    owner_ct_id=content_type_id,
                    owner_id__in=my_content_ids,
                    uuid__in=uuid_list
                )
            )
        else:
            query = Q(
                owner_ct_id=user_ct,
                owner_id=self.me.id,
                uuid__in=uuid_list
            )
        MediaModel.objects.filter(
            query
        ).update(**{
            'deleted': True,
            'updated_at': now()
        })
