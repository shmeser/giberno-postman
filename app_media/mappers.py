import pytils as pytils

from app_media.entities import FileEntity
from app_media.forms import FileForm


class RequestToMediaEntity:
    @staticmethod
    def map(request):
        form = FileForm(request.POST, request.FILES)
        entities = []

        if form.is_valid():  # Проверяем, все ли обязательные поля пришли
            for file_ in form.files.getlist('file'):
                entity = FileEntity()
                entity.owner = request.user.id

                exs = file_.name.split('.')
                if exs.__len__() > 1:
                    exs = exs[-1].lower()  # расширение файла всегда стоит в конце, поэтому, берем элемент -1 индекса
                else:
                    exs = ''
                file_.name = pytils.translit.slugify(
                    file_.name) + '.' + exs  # переводим название файла на английский язык

                entity.file = file_
                entity.content_type = file_.content_type

                if form.cleaned_data.get('uuid', None):
                    entity.uuid = form.cleaned_data['uuid']
                else:
                    entity.uuid = uuid.uuid4()

                if form.cleaned_data.get('type', None):
                    entity.type = int(form.cleaned_data['type'])
                else:
                    entity.type = MediaType.IMAGE

                print('FILE TYPE: ' + str(form.cleaned_data['type']))
                print('FILE CONTENT TYPE: ' + str(file_.content_type))

                content_type = str(file_.content_type).split('/')[0]

                if entity.type == MediaType.IMAGE:  # проверяем на тип файла, который нам пришел
                    entity.text = 'Изображение'
                    if content_type not in ['image']:
                        raise HttpException(detail=Errors.MESSAGE_TYPE_ERROR.name,
                                            status_code=Errors.MESSAGE_TYPE_ERROR)
                elif entity.type == MediaType.AUDIO:
                    entity.text = 'Аудиозапись'
                    if content_type not in ['audio']:
                        raise HttpException(detail=Errors.MESSAGE_TYPE_ERROR.name,
                                            status_code=Errors.MESSAGE_TYPE_ERROR)
                elif entity.type == MediaType.VIDEO:
                    entity.text = 'Видеозапись'
                    if content_type not in ['video']:
                        raise HttpException(detail=Errors.MESSAGE_TYPE_ERROR.name,
                                            status_code=Errors.MESSAGE_TYPE_ERROR)
                else:
                    raise HttpException(detail=Errors.MESSAGE_TYPE_ERROR.name,
                                        status_code=Errors.MESSAGE_TYPE_ERROR)
                entities.append(entity)
            return entities
        else:
            raise HttpException(detail=Errors.BAD_REQUEST.name,
                                status_code=Errors.BAD_REQUEST)
