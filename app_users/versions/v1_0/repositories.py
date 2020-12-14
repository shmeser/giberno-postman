import re

from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken

from app_users.entities import JwtTokenEntity, SocialEntity
from app_users.enums import AccountType
from app_users.models import SocialModel, UserProfile, JwtToken
from backend.errors.enums import RESTErrors
from backend.errors.exceptions import EntityDoesNotExistException
from backend.errors.http_exception import HttpException
from backend.mixins import MasterRepository
from backend.repositories import BaseRepository


class UsersRepository(object):
    @staticmethod
    def get_reference_user(reference_code):
        return UserProfile.objects.filter(uuid__icontains=reference_code, deleted=False).first()


class AuthRepository:

    @staticmethod
    def get_or_create_social_user(social_data: SocialEntity, account_type=AccountType.SELF_EMPLOYED,
                                  reference_code=None):

        # Проверка реферального кода
        reference_user = None
        if reference_code:
            reference_user = UsersRepository.get_reference_user(reference_code)
            if reference_user is None:
                raise HttpException(detail='Невалидный реферальный код', status_code=RESTErrors.BAD_REQUEST)

        # Создаем способ авторизации
        social, created = SocialModel.objects.get_or_create(
            social_id=social_data.social_id, type=social_data.social_type, defaults=social_data.get_kwargs()
        )

        # Получаем или создаем пользователя
        defaults = {
            'reg_reference': reference_user,
            'reg_reference_code': reference_code,
            'phone': social_data.phone,
            'email': social_data.email,
            'first_name': social_data.first_name,
            'last_name': social_data.last_name,
            'middle_name': social_data.middle_name,
            'username': social_data.username,
        }

        # Проверка типа аккаунта, отсылаемого при авторизации
        if account_type is not None and AccountType.has_value(account_type):
            defaults['account_type'] = account_type

        user, created = UserProfile.objects.get_or_create(socialmodel=social, defaults=defaults)

        if created:
            social.user = user
            social.save()

        if user.account_type != account_type:
            raise HttpException(
                detail='Данным способом уже зарегистрирован пользователь с другой ролью',
                status_code=RESTErrors.FORBIDDEN
            )

        # Создаем модель настроек
        # TODO
        return user, created


class SocialModelRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__(SocialModel)

    @staticmethod
    def create(**kwargs):
        return SocialModel.objects.create(**kwargs)

    def filter_by_kwargs(self, **kwargs):
        return super().filter_by_kwargs(kwargs)


class JwtRepository:
    def __init__(self, headers=None):
        self.app_version = headers['App'] if headers and 'App' in headers else None
        self.platform_name = headers['Platform'] if headers and 'Platform' in headers else None
        self.vendor = headers['Vendor'] if headers and 'Vendor' in headers else None

    @classmethod
    def get_or_create_jwt_token(cls, user: UserProfile):
        try:
            return cls.get_jwt_token(user)
        except EntityDoesNotExistException:
            return cls().create_jwt_token(user)

    def create_jwt_token(self, user: UserProfile):
        refresh = RefreshToken.for_user(user)

        refresh_token = str(refresh)
        access_token = str(refresh.access_token)

        return JwtToken.objects.create(
            user=user, access_token=access_token, refresh_token=refresh_token, app_version=self.app_version,
            platform_name=self.platform_name, vendor=self.vendor
        )

    @staticmethod
    def get_jwt_token(user: UserProfile):
        try:
            return JwtToken.objects.get(user=user)
        except JwtToken.DoesNotExist:
            raise EntityDoesNotExistException()

    @staticmethod
    def remove_old(user):
        JwtToken.objects.filter(**{'user_id': user.id}).delete()

    @staticmethod
    def refresh(refresh_token, new_access_token):
        # TODO нужно доработать, если потребуется ROTATE_REFRESH_TOKENS=True и BLACKLIST_AFTER_ROTATION=True
        pair = JwtToken.objects.filter(**{'refresh_token': refresh_token}).first()
        if pair:
            pair.access_token = new_access_token
            pair.save()

        return pair

    def create_jwt_pair(self, user):
        refresh = RefreshToken.for_user(user)

        refresh_token = str(refresh)
        access_token = str(refresh.access_token)

        return JwtToken.objects.create(
            **JwtTokenEntity(
                user, access_token, refresh_token, self.app_version, self.platform_name, self.vendor
            ).get_kwargs()
        )

    @staticmethod
    def get_user(token):
        try:
            return JwtToken.objects.get(access_token=token).user
        except JwtToken.DoesNotExist:
            raise EntityDoesNotExistException()

    @staticmethod
    def get_jwt_pair(user):
        refresh = RefreshToken.for_user(user)

        refresh_token = str(refresh)
        access_token = str(refresh.access_token)

        return JwtToken.objects.create(**JwtTokenEntity(user, access_token, refresh_token).get_kwargs())


class ProfileRepository(MasterRepository):
    model = UserProfile

    def get_by_id(self, record_id):
        try:
            return self.Model.objects.get(id=record_id, is_staff=False)
        except self.Model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail='Объект %s с ID=%d не найден' % (self.Model._meta.verbose_name, record_id)
            )

    def update_or_create(self, **kwargs):
        try:
            shop_networks = kwargs.pop('networks')
            nutrients = kwargs.pop('nutrients')
            possible_nutrients = kwargs.pop('possible_nutrients')
            image_url = kwargs.pop('image')
            category = kwargs.pop('category')

            product = super().update_or_create(**kwargs)
            product.shop_networks.clear()
            product.nutrients.clear()
            product.possible_nutrients.clear()

            if shop_networks:
                product.shop_networks.add(
                    *ShopNetworksRepository().filter_by_kwargs({'external_id__in': shop_networks}))
            if nutrients:
                product.nutrients.add(*NutrientsRepository().filter_by_kwargs({'external_id__in': nutrients}))
            if possible_nutrients:
                product.possible_nutrients.add(
                    *NutrientsRepository().filter_by_kwargs({'external_id__in': possible_nutrients}))
            if category is not None:
                try:
                    product.category = CategoriesRepository().get_by_external_id(category[0])
                except HttpException:
                    pass

            if product.nutrients.filter(title__icontains='соль'):
                product.is_salt = True

            if product.nutrients.filter(title__icontains='сахар'):
                product.is_sugar = True

            # product's diet should be True only if all fields of its nutrients is also True
            # `product.nutrients.values_list('lacto', flat=True)` can't be empty because at least it has default value.
            product.lacto = all(product.nutrients.values_list('lacto', flat=True))
            product.ovo = all(product.nutrients.values_list('ovo', flat=True))
            product.vegan = all(product.nutrients.values_list('vegan', flat=True))
            if not product.lacto or not product.ovo:
                product.lacto_ovo = False

            if image_url:
                if product.image is None:
                    self.__assign_image_to_product(product=product, image_url=image_url)
                else:
                    # to avoid re-assignment of the same image
                    if product.image.file_url != image_url:
                        self.__assign_image_to_product(product=product, image_url=image_url)
            else:
                product.image = MediaRepository().get_random_placeholder()
            product.save()

        except Exception as e:
            print(f'[ADDED ERROR], ex_id={kwargs.get("external_id")} {str(e)}')

    def filter_by_title(self, product_title, additional_filters):
        title_filters = (
                Q(barcode__istartswith=product_title) |
                # Полнотекстовый поиск с векторами postgres (для работы нужен обязательно 'django.contrib.postgres')
                Q(title__search=product_title.strip()) |
                Q(title__iregex=f"(^|[\\s\\.''\"]){product_title}([\\s\\.''\"]|(\\Z|.*\\s))")
        )

        return self.Model.objects.filter(
            title_filters, **additional_filters, nutrients__isnull=False
        ).distinct()

    def order_by_title(self, products, requested_title):
        rating_storage = []
        splitted_requested_title = requested_title.split()
        requested_title = requested_title.lower()

        for product in products:
            cleared_product_title = re.sub(r'\.|\'|\"|\,|\;|\:', '', product.title.lower())
            splitted_product_title = cleared_product_title.split(' ')

            for product_title_word in splitted_product_title:
                if len(splitted_requested_title) > 1:
                    if cleared_product_title == requested_title:
                        index = 0
                    elif cleared_product_title.startswith(requested_title):
                        index = 1
                    elif requested_title in cleared_product_title:
                        index = 2
                    else:
                        index = 3
                    rating_storage.append({'index': index, 'product': product})
                    break
                else:
                    if requested_title.lower() == product_title_word.lower():
                        rating_storage.append({
                            'index': splitted_product_title.index(requested_title),
                            'product': product
                        })
                        break

        rating_storage.sort(key=lambda x: x.get('index'))
        return [i.get('product') for i in rating_storage]
