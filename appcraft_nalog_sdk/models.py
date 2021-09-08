import uuid

from django.db import models
from django.utils import timezone

from appcraft_nalog_sdk.enums import NalogUserStatus
from appcraft_nalog_sdk.errors import OrderIdNotFoundException, MessageIdNotFoundException, ReceiptIdNotFoundException


class NalogBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(null=True, blank=True, verbose_name='Ошибка')

    def set_error(self, error):
        self.error_message = error
        self.save()

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()
        return self

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.updated_at = timezone.now()
        super().save(force_insert, force_update, using, update_fields)

    class Meta:
        abstract = True


class NalogUser(NalogBaseModel):
    inn = models.CharField(max_length=12, verbose_name='ИНН пользователя')
    first_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Имя')
    second_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Фамилия')
    patronymic = models.CharField(max_length=255, null=True, blank=True, verbose_name='Отчество')
    phone_number = models.CharField(max_length=20, null=True, blank=True, verbose_name='Номер телефона')
    bank_id = models.IntegerField(null=True, blank=True, verbose_name='ID банка из системы быстрых платежей')
    status = models.IntegerField(choices=NalogUserStatus.choices, default=NalogUserStatus.UNKNOWN,
                                 verbose_name='Статус самозанятого')
    is_tax_payment = models.BooleanField(default=False, verbose_name='Платим ли налоги за пользователя')
    added_to_registry = models.BooleanField(default=False,
                                            verbose_name='Пользователь добавлен в рееестр самозанятых Тинькофф')

    @classmethod
    def get_or_create(cls, inn):
        return cls.objects.get_or_create(inn=inn)[0]

    def update_status(self, status):
        self.status = status
        self.save()

    def update_tax_payment(self, value):
        self.is_tax_payment = value
        self.save()

    def update_bank_id(self, bank_id):
        self.bank_id = bank_id
        self.save()

    def update(self, first_name, second_name, patronymic, phone_number):
        self.first_name = first_name
        self.second_name = second_name
        self.patronymic = patronymic
        self.phone_number = phone_number
        self.save()

    def __str__(self):
        return self.inn

    class Meta:
        db_table = 'appcraft_nalog_sdk_users'
        verbose_name = 'Налоговый пользователь'
        verbose_name_plural = 'Налоговые пользователи'


class NalogNotificationModel(NalogBaseModel):
    user = models.ForeignKey(NalogUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    notification_id = models.IntegerField(verbose_name='ID Уведомления в ФНС')
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Сообщение')
    status = models.CharField(max_length=255, verbose_name='Статус уведомления')

    @classmethod
    def create(cls, inn, notification_id, title, message, status, created_at, updated_at):
        notification = cls.objects.get_or_create(
            user=NalogUser.get_or_create(inn),
            notification_id=notification_id,
            title=title,
            message=message
        )[0]

        notification.status = status
        notification.updated_at = updated_at
        notification.created_at = created_at
        notification.save()

    @classmethod
    def get_unread_notifications(cls, inn):
        return cls.objects.filter(user__inn=inn, status='NEW')

    def __str__(self):
        return f'{self.user}: {self.title}'

    class Meta:
        db_table = 'appcraft_nalog_notifications'
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'


class NalogRequestModel(NalogBaseModel):
    class RequestNameChoice(models.TextChoices):
        AUTH_REQUEST = 'AuthRequest'
        GET_TAXPAYER_STATUS_REQUEST = 'GetTaxpayerStatusRequest'
        GET_NOTIFICATIONS_REQUEST = 'GetNotificationsRequest'
        POST_BIND_PARTNER_WITH_INN_REQUEST = 'PostBindPartnerWithInnRequest'
        GET_BIND_PARTNER_STATUS_REQUEST = 'GetBindPartnerStatusRequest'
        POST_INCOME_REQUEST_V2 = 'PostIncomeRequestV2'
        POST_CANCEL_RECEIPT_REQUEST_V2 = 'PostCancelReceiptRequestV2'
        GET_GRANTED_PERMISSIONS_REQUEST = 'GetGrantedPermissionsRequest'
        GET_CANCEL_INCOME_REASONS_LIST_REQUEST = 'GetCancelIncomeReasonsListRequest'
        POST_PLATFORM_REGISTRATION_REQUEST = 'PostPlatformRegistrationRequest'
        POST_NOTIFICATIONS_ACK_REQUEST = 'PostNotificationsAckRequest'
        GET_NEWLY_UNBOUND_TAXPAYERS_REQUEST = 'GetNewlyUnboundTaxpayersRequest'
        GET_INCOME_REQUEST_V2 = 'GetIncomeRequestV2'
        GET_PAYMENT_DOCUMENTS_REQUEST = 'GetPaymentDocumentsRequest'

    class StatusChoice(models.TextChoices):
        PROCESSING = 'PROCESSING', 'В процессе'
        COMPLETED = 'COMPLETED', 'Выполнен',
        NOT_FOUND = 'NOT_FOUND', 'MessageID истек или не найден'

    user = models.ForeignKey(NalogUser, on_delete=models.PROTECT, null=True, blank=True,
                             verbose_name='Пользователь, над которым совершается операция')
    name = models.TextField(choices=RequestNameChoice.choices, verbose_name='Запрос')
    request_xml = models.TextField(verbose_name='Полный XML запроса')
    message_id = models.CharField(null=True, blank=True, max_length=255, verbose_name='Message ID')
    response_xml = models.TextField(null=True, blank=True, verbose_name='Полный XML ответа GetMessage')
    status = models.TextField(choices=StatusChoice.choices, default=StatusChoice.PROCESSING,
                              verbose_name='Статус выполнения')

    @classmethod
    def create(cls, name, request_data, inn=None):
        user = None
        if inn:
            user = NalogUser.get_or_create(inn)
        return cls.objects.create(name=name, request_xml=request_data, user=user)

    @classmethod
    def get_processing_requests(cls):
        return cls.objects.filter(status=cls.StatusChoice.PROCESSING).exclude(name=cls.RequestNameChoice.AUTH_REQUEST)

    @classmethod
    def get_by_message_id(cls, message_id):
        request_model = cls.objects.filter(message_id=message_id).last()
        if request_model is None:
            raise MessageIdNotFoundException()
        return request_model

    def update_message_id(self, message_id):
        self.message_id = message_id
        self.save()

    def update_response_data(self, response_data):
        self.response_xml = response_data
        self.save()

    def update_status(self, status, response_data):
        self.status = status
        self.response_xml = response_data
        self.save()

    def __str__(self):
        return f'{self.message_id}, {self.created_at}, {self.updated_at}'

    class Meta:
        db_table = 'appcraft_nalog_sdk_request_logs'
        verbose_name = 'Лог запроса'
        verbose_name_plural = 'Логи запросов'


class NalogBindPartnerRequestModel(NalogBaseModel):
    class StatusChoices(models.TextChoices):
        COMPLETED = 'COMPLETED', 'Заявка на выдачу прав рассмотрена'
        FAILED = 'FAILED', 'Заявка на выдачу прав отклонена'
        IN_PROGRESS = 'IN_PROGRESS', 'Заявка на выдачу прав находится на рассмотрении'

    user = models.ForeignKey(NalogUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    order_id = models.CharField(max_length=255, verbose_name='ID заявки')
    status = models.CharField(max_length=255, choices=StatusChoices.choices, default=StatusChoices.IN_PROGRESS,
                              verbose_name='Статус заявки')

    @classmethod
    def create(cls, inn, order_id):
        return cls.objects.create(
            user=NalogUser.get_or_create(inn),
            order_id=order_id
        )

    def update_status(self, status):
        if status['Result'] == self.StatusChoices.COMPLETED and 'TAX_PAYMENT' in status['Permissions']:
            self.user.is_tax_payment = True
            self.user.update_status(NalogUserStatus.ATTACHED_TO_A_PARTNER)
            self.user.save()

        self.status = status['Result']
        self.save()

    @classmethod
    def get_bind_request(cls, inn):
        bind_request_model = NalogBindPartnerRequestModel.objects.filter(user__inn=inn).last()
        if bind_request_model is None:
            raise OrderIdNotFoundException()
        return bind_request_model

    def __str__(self):
        return f'{self.user}, {self.order_id}, {self.status}'

    class Meta:
        db_table = 'appcraft_nalog_sdk_bind_partner_requests'
        verbose_name = 'Заявка на привязку к партнеру'
        verbose_name_plural = 'Заявки на привязку к партнеру'


class NalogIncomeCancelReasonModel(NalogBaseModel):
    class DefaultCancelReason(models.TextChoices):
        USER = 'USER', 'Пользователь отменил чек из ЛК Мой налог'

    code = models.CharField(max_length=255, verbose_name='Код отмены чека')
    description = models.TextField(verbose_name='Описание причины отмены')

    @classmethod
    def update_reasons(cls, reasons):
        cls.objects.exclude(code=cls.DefaultCancelReason.USER).update(deleted_at=timezone.now())
        for reason in reasons:
            new_reason, _ = cls.objects.get_or_create(code=reason['code'])
            new_reason.description = reason['description']
            new_reason.deleted_at = None
            new_reason.save()

        cls.objects.get_or_create(code=cls.DefaultCancelReason.USER, description=cls.DefaultCancelReason.USER.label)

    @classmethod
    def get_by_code(cls, reason):
        reason, _ = cls.objects.get_or_create(code=reason)
        return reason

    def __str__(self):
        return f'{self.code}: {self.description}'

    class Meta:
        db_table = 'appcraft_nalog_sdk_cancel_reasons'
        verbose_name = 'Причина'
        verbose_name_plural = 'Причины отмены чеков'


class NalogIncomeRequestModel(NalogBaseModel):
    uuid = models.UUIDField(verbose_name='Уникальный идентификатор операции')
    message_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='MessageID')
    user = models.ForeignKey(NalogUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    amount = models.FloatField(verbose_name='Сумма дохода')
    name = models.CharField(max_length=255, verbose_name='Название дохода')
    receipt_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='ID чека')
    link = models.CharField(max_length=255, null=True, blank=True, verbose_name='Ссылка на чек')
    operation_time = models.DateTimeField(verbose_name='Дата совершение услуги')
    request_time = models.DateTimeField(verbose_name='Дата совершение услуги')
    latitude = models.CharField(max_length=255, null=True, blank=True)
    longitude = models.CharField(max_length=255, null=True, blank=True)
    is_canceled = models.BooleanField(default=False, verbose_name='Отменен/Аннулирован')
    canceled_reason = models.ForeignKey(NalogIncomeCancelReasonModel, on_delete=models.PROTECT, null=True, blank=True,
                                        verbose_name='Причина аннулирования')

    @classmethod
    def get_by_id(cls, receipt_id):
        nalog_request_model = cls.objects.filter(receipt_id=receipt_id).last()
        if nalog_request_model is None:
            raise ReceiptIdNotFoundException()
        return nalog_request_model

    @classmethod
    def create(cls, inn, amount, name, operation_time, request_time, latitude=None, longitude=None):
        return cls.objects.create(
            uuid=uuid.uuid4(),
            user=NalogUser.get_or_create(inn),
            amount=amount,
            name=name,
            operation_time=operation_time,
            request_time=request_time,
            latitude=latitude,
            longitude=longitude
        )

    def update_receipt(self, receipt_id, link):
        self.receipt_id = receipt_id
        self.link = link
        self.save()

    def cancel(self):
        self.is_canceled = True
        self.save()

    def set_canceled_reason(self, reason):
        reason = NalogIncomeCancelReasonModel.get_by_code(reason)
        self.canceled_reason = reason
        self.save()

    def set_message_id(self, message_id):
        if self.message_id is None:
            self.message_id = message_id
            self.save()

    @classmethod
    def get_by_message_id(cls, message_id):
        nalog_request_model = cls.objects.filter(message_id=message_id).last()
        if nalog_request_model is None:
            raise MessageIdNotFoundException()
        return nalog_request_model

    def __str__(self):
        return f'{self.user}, {self.receipt_id}, {self.link}'

    class Meta:
        db_table = 'appcraft_nalog_sdk_income_requests'
        verbose_name = 'Регистрация дохода'
        verbose_name_plural = 'Регистрация доходов'

class NalogDocumentModel(NalogBaseModel):
    user = models.ForeignKey(NalogUser, on_delete=models.CASCADE, verbose_name='Пользователь')
    type = models.TextField(null=True, blank=True, verbose_name='Тип платежного документа')
    index = models.TextField(null=True, blank=True, verbose_name='Индекс документа (УИН)')
    full_name = models.TextField(null=True, blank=True, verbose_name='ФИО налогоплательщика')
    address = models.TextField(null=True, blank=True, verbose_name='Адрес места жительства')
    inn = models.TextField(null=True, blank=True, verbose_name='ИНН налогоплательщика')
    # TODO как не потерять копейки?
    amount = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=10, verbose_name='Сумма к оплате')
    recipient_bank_name = models.TextField(null=True, blank=True, verbose_name='Банк получателя')
    recipient_bank_bik = models.TextField(null=True, blank=True, verbose_name='БИК банка получателя')
    recipient_bank_account_number = models.TextField(null=True, blank=True, verbose_name='Сумма к оплате')
    recipient = models.TextField(null=True, blank=True, verbose_name='Получатель')
    recipient_account_number = models.TextField(null=True, blank=True, verbose_name='Номер счёта получателя')
    recipient_inn = models.TextField(null=True, blank=True, verbose_name='ИНН получателя')
    recipient_kpp = models.TextField(null=True, blank=True, verbose_name='КПП получателя')
    kbk = models.TextField(null=True, blank=True, verbose_name='Kbk')
    oktmo = models.TextField(null=True, blank=True, verbose_name='Oktmo')
    code_101 = models.TextField(null=True, blank=True, verbose_name='Код для поля 101')
    code_106 = models.TextField(null=True, blank=True, verbose_name='Код для поля 106')
    code_107 = models.TextField(null=True, blank=True, verbose_name='Код для поля 107')
    code_110 = models.TextField(null=True, blank=True, verbose_name='Код для поля 110')
    due_date = models.DateTimeField(null=True, blank=True, verbose_name='Оплатить до')
    create_time = models.DateTimeField(null=True, blank=True, verbose_name='Дата/Время создания документа')
    source_id = models.TextField(null=True, blank=True,
                                 verbose_name='Внутренний идентификатор источника документа в ПП НПД')

    def __str__(self):
        return f'{self.user}: {self.create_time}'

    class Meta:
        db_table = 'appcraft_nalog_sdk_documents'
        verbose_name = 'Документ'
        verbose_name_plural = 'Платежные документы'
