import uuid

import xmltodict
from loguru import logger

from app_users.enums import NotificationType, NotificationIcon, NotificationAction
from app_users.models import Notification
from appcraft_nalog_sdk import request_fabric
from appcraft_nalog_sdk.enums import NalogUserStatus
from appcraft_nalog_sdk.errors import ErrorController, TaxpayerUnregisteredException, TaxpayerUnboundException, \
    MessageIdNotFoundException, TaxpayerAlreadyBoundException, PartnerDenyException, RequestValidationException, \
    DuplicateException, PermissionNotGrantedException, AlreadyDeletedException, ReceiptIdNotFoundException
from appcraft_nalog_sdk.models import NalogRequestModel, NalogBindPartnerRequestModel, NalogNotificationModel, \
    NalogIncomeRequestModel, NalogUser, NalogIncomeCancelReasonModel, NalogDocumentModel, NalogOfflineKeyModel
from backend.controllers import PushController


class ResponseRouter:
    def __init__(self, message_id, sdk_instance) -> None:
        super().__init__()
        self.__get_request_model(message_id)
        self.__get_message()
        self.sdk_instance = sdk_instance

    def route(self):
        self.__check_process()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.GET_TAXPAYER_STATUS_REQUEST:
            return self.get_status_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.POST_BIND_PARTNER_WITH_INN_REQUEST:
            return self.post_bind_partner_with_inn_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.GET_BIND_PARTNER_STATUS_REQUEST:
            return self.get_bind_partner_status_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.POST_INCOME_REQUEST_V2:
            return self.post_income_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.POST_CANCEL_RECEIPT_REQUEST_V2:
            return self.post_cancel_receipt_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.GET_GRANTED_PERMISSIONS_REQUEST:
            return self.get_granted_permissions_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.GET_CANCEL_INCOME_REASONS_LIST_REQUEST:
            return self.get_cancel_income_reasons_list_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.POST_PLATFORM_REGISTRATION_REQUEST:
            return self.post_platform_registration_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.GET_NOTIFICATIONS_REQUEST:
            return self.get_notifications_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.POST_NOTIFICATIONS_ACK_REQUEST:
            return self.read_notifications_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.GET_NEWLY_UNBOUND_TAXPAYERS_REQUEST:
            return self.get_newly_unbound_taxpayers_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.GET_INCOME_REQUEST_V2:
            return self.get_income_request_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.GET_PAYMENT_DOCUMENTS_REQUEST:
            return self.get_payment_documents_response()

        if self.request_model.name == NalogRequestModel.RequestNameChoice.GET_KEYS_REQUEST:
            return self.get_keys_response()

    def get_status_response(self, ):
        try:
            ErrorController.check_error(self.message, self.request_model.user)

            if 'GetTaxpayerStatusResponse' in self.message:
                self.request_model.user.update_status(NalogUserStatus.ATTACHED_TO_A_PARTNER)
                self.request_model.user.update(
                    first_name=self.message['GetTaxpayerStatusResponse']['FirstName'],
                    second_name=self.message['GetTaxpayerStatusResponse']['SecondName'],
                    patronymic=self.message['GetTaxpayerStatusResponse']['Patronymic'],
                    phone_number=self.message['GetTaxpayerStatusResponse']['Phone']
                )
        except TaxpayerUnregisteredException:
            pass
        except TaxpayerUnboundException:
            pass
        except RequestValidationException as error:
            self.request_model.user.set_error(error.detail)

    def post_bind_partner_with_inn_response(self):
        try:
            ErrorController.check_error(self.message, self.request_model.user)
            if 'PostBindPartnerWithInnResponse' in self.message:
                order_id = self.message['PostBindPartnerWithInnResponse']['Id']
                NalogBindPartnerRequestModel.create(self.request_model.user.inn, order_id)
                return order_id
        except TaxpayerUnregisteredException:
            return False
        except TaxpayerAlreadyBoundException:
            return False
        except PartnerDenyException:
            return False
        except RequestValidationException as error:
            self.request_model.user.set_error(error.detail)

    def get_bind_partner_status_response(self):
        nalog_bind_partner_request_model = NalogBindPartnerRequestModel.objects.filter(
            user=self.request_model.user).last()
        try:
            if nalog_bind_partner_request_model is None:
                return False
            ErrorController.check_error(self.message)
            if 'GetBindPartnerStatusResponse' in self.message:
                status = self.message['GetBindPartnerStatusResponse']
                nalog_bind_partner_request_model.update_status(status)
                is_tax_payment = 'TAX_PAYMENT' in self.message['GetBindPartnerStatusResponse'][
                    'Permissions']
                self.request_model.user.update_tax_payment(is_tax_payment)
                return status
        except TaxpayerUnregisteredException:
            return False
        except PartnerDenyException:
            return False
        except RequestValidationException as error:
            nalog_bind_partner_request_model.set_error(error.detail)

    def post_income_response(self):
        nalog_request_model = NalogIncomeRequestModel.get_by_message_id(self.request_model.message_id)

        try:
            ErrorController.check_error(self.message, self.request_model.user)
            if 'PostIncomeResponseV2' in self.message:
                receipt_id = self.message['PostIncomeResponseV2']['ReceiptId']
                link = self.message['PostIncomeResponseV2']['Link']
                nalog_request_model.update_receipt(receipt_id, link)
                return link
        except TaxpayerUnregisteredException as e:
            nalog_request_model.set_error(e.detail)
        except PartnerDenyException as e:
            nalog_request_model.set_error(e.detail)
        except DuplicateException as e:
            nalog_request_model.set_error(e.detail)
        except PermissionNotGrantedException as e:
            nalog_request_model.set_error(e.detail)
        except RequestValidationException as e:
            nalog_request_model.set_error(e.detail)

    def post_cancel_receipt_response(self):
        nalog_request_model = NalogRequestModel.get_by_message_id(self.request_model.message_id)

        try:
            ErrorController.check_error(self.message, self.request_model.user)
            if 'PostCancelReceiptResponseV2' in self.message \
                    and self.message['PostCancelReceiptResponseV2']['RequestResult'] == 'DELETED':
                nalog_request_model.cancel()
                return True
        except TaxpayerUnregisteredException as e:
            nalog_request_model.set_error(e.detail)
            pass
        except PartnerDenyException as e:
            nalog_request_model.set_error(e.detail)
            pass
        except AlreadyDeletedException as e:
            nalog_request_model.set_error(e.detail)
            pass
        except RequestValidationException as e:
            nalog_request_model.set_error(e.detail)
            pass

    def get_granted_permissions_response(self):
        try:
            ErrorController.check_error(self.message)
            if 'GetGrantedPermissionsResponse' in self.message:
                is_tax_payment = 'TAX_PAYMENT' in self.message['GetGrantedPermissionsResponse'][
                    'GrantedPermissionsList']
                self.request_model.user.update_tax_payment(is_tax_payment)
        except TaxpayerUnregisteredException:
            pass
        except TaxpayerUnboundException:
            pass
        except RequestValidationException:
            pass

    def get_cancel_income_reasons_list_response(self):
        ErrorController.check_error(self.message)
        if 'GetCancelIncomeReasonsListResponse' in self.message:
            reasons = []
            for code in self.message['GetCancelIncomeReasonsListResponse']['Codes']:
                reasons.append({'code': code['Code'], 'description': code['Description']})
            NalogIncomeCancelReasonModel.update_reasons(reasons)

    def post_platform_registration_response(self):
        try:
            ErrorController.check_error(self.message)
            if 'PostPlatformRegistrationResponse' in self.message:
                return self.message['PostPlatformRegistrationResponse']['PartnerID']
        except RequestValidationException:
            return False

        return False

    def get_notifications_response(self):
        try:
            ErrorController.check_error(self.message, self.request_model.user)
            if 'GetNotificationsResponse' in self.message:

                notifications_links = []

                profile = None

                message = None
                title = None
                notification_uuid = uuid.uuid4()

                subject_id = None
                notification_type = NotificationType.NALOG.value
                action = NotificationAction.APP.value
                icon_type = NotificationIcon.DEFAULT.value
                is_sound_enabled = True

                for notification in self.message['GetNotificationsResponse']['notificationsResponse']['notif']:

                    n, created = NalogNotificationModel.create(
                        inn=self.message['GetNotificationsResponse']['notificationsResponse']['inn'],
                        notification_id=notification['id'],
                        title=notification['title'],
                        message=notification['message'],
                        status=notification['status'],
                        created_at=notification['createdAt'],
                        updated_at=notification['updatedAt']
                    )
                    # дублируем оповещения налоговой из sdk в основную таблицу
                    if created:
                        profile = n.user.profiles.last()  # Берем последнего привязанного пользователя из основной бд

                        title = notification['title']
                        message = notification['message']
                        notification_uuid = uuid.uuid4()

                        if profile:
                            notifications_links.append(
                                Notification(
                                    uuid=notification_uuid,
                                    user_id=profile.id,
                                    subject_id=subject_id,
                                    title=title,
                                    message=message,
                                    type=notification_type,
                                    action=action,
                                    push_tokens_android=[],
                                    push_tokens_ios=[],
                                    icon_type=icon_type,
                                    sound_enabled=is_sound_enabled,
                                    nalog_notification=n
                                )
                            )

                Notification.objects.bulk_create(notifications_links)  # Массовое создание уведомлений
                # TODO Переделать на отправку 3-5 уведомлений последних, отсортировать по nalog notification_id
                if notifications_links:
                    # Отправляем только 1 пуш последний, чтобы не отправить лавину пушей при первом переносе уведомлений
                    # Сами записи в бд создадутся на все перенесенные
                    PushController().send_message(
                        uuid=notification_uuid,
                        users_to_send=[profile],
                        title=title,
                        message=message,
                        common_uuid=notification_uuid,
                        action=action,
                        subject_id=subject_id,
                        notification_type=notification_type,
                        icon_type=icon_type
                    )

        except RequestValidationException:
            pass
        except TaxpayerUnboundException:
            pass

    def read_notifications_response(self):
        try:
            ErrorController.check_error(self.message)
            if 'PostNotificationsAckResponse' in self.message:
                return True
        except RequestValidationException:
            return False
        except TaxpayerUnboundException:
            pass

    def get_newly_unbound_taxpayers_response(self):
        try:
            ErrorController.check_error(self.message)
            if 'GetNewlyUnboundTaxpayersResponse' in self.message:
                if 'Taxpayers' not in self.message['GetNewlyUnboundTaxpayersResponse']:
                    return

                if isinstance(self.message['GetNewlyUnboundTaxpayersResponse']['Taxpayers'], list):
                    for user in self.message['GetNewlyUnboundTaxpayersResponse']['Taxpayers']:
                        NalogUser.get_or_create(user['Inn']).update_status(NalogUserStatus.UNKNOWN)
                else:
                    self.sdk_instance.get_status(self.message['GetNewlyUnboundTaxpayersResponse']['Taxpayers']['Inn'])
                if self.message['GetNewlyUnboundTaxpayersResponse']['HasMore'] == 'true':
                    request_data = request_fabric.get_message_request(self.request_model.request_xml)[
                        'tns:GetNewlyUnboundTaxpayersRequest']
                    self.sdk_instance.get_newly_unbound_taxpayers_request(
                        from_date=request_data['tns:From'],
                        to_date=request_data['tns:To'],
                        offset=int(request_data['tns:Limit']) + int(
                            request_data['tns:Offset']),
                    )

        except RequestValidationException:
            return False

    def get_income_request_response(self):
        try:
            ErrorController.check_error(self.message, self.request_model.user)
            if 'GetIncomeResponseV2' in self.message:
                if 'Receipts' not in self.message['GetIncomeResponseV2']:
                    return

                if isinstance(self.message['GetIncomeResponseV2']['Receipts'], list):
                    for receipt in self.message['GetIncomeResponseV2']['Receipts']:
                        self.__cancel_receipt(receipt)
                else:
                    self.__cancel_receipt(self.message['GetIncomeResponseV2']['Receipts'])
        except RequestValidationException:
            return False

    def __cancel_receipt(self, receipt):
        try:
            if 'CancelationTime' in receipt:
                nalog_income_request = NalogIncomeRequestModel.get_by_id(receipt['ReceiptId'])
                nalog_income_request.cancel()
                nalog_income_request.set_canceled_reason(NalogIncomeCancelReasonModel.DefaultCancelReason.USER)
        except ReceiptIdNotFoundException:
            nalog_income_request = NalogIncomeRequestModel.create(
                inn=self.request_model.user.inn,
                amount=receipt['Services']['Amount'],
                name=receipt['Services']['Name'],
                operation_time=receipt['OperationTime'],
                request_time=receipt['RequestTime'],
            )
            nalog_income_request.update_receipt(receipt['ReceiptId'], receipt['Link'])
            if 'CancelationTime' in receipt:
                nalog_income_request.cancel()
                nalog_income_request.set_canceled_reason(NalogIncomeCancelReasonModel.DefaultCancelReason.USER)

    def get_payment_documents_response(self):
        try:
            ErrorController.check_error(self.message)
            if 'GetPaymentDocumentsResponse' in self.message \
                    and 'DocumentsList' in self.message['GetPaymentDocumentsResponse']:
                users = self.message['GetPaymentDocumentsResponse']['DocumentsList']

                for user in users:
                    if 'DocumentList' not in user:
                        continue
                    inn = user['Inn']
                    if isinstance(user['DocumentList'], list):
                        for document in user['DocumentList']:
                            self.__save_document(inn, document)
                    else:
                        self.__save_document(inn, user['DocumentList'])
        except RequestValidationException:
            return False

    def get_keys_response(self):
        try:
            logger.debug(self.message)
            ErrorController.check_error(self.message, self.request_model.user)
            if 'GetKeysResponse' in self.message:
                for key in self.message['GetKeysResponse']:
                    for key_record in key:
                        if 'SequenceNumber' not in key_record:
                            continue

                        NalogOfflineKeyModel.create(
                            inn=key['inn'],
                            sequence_number=key_record['SequenceNumber'],
                            base64_key=key_record['Base64Key'],
                            expire_time=key_record['ExpireTime']
                        )
        except RequestValidationException:
            pass
        except TaxpayerUnboundException:
            pass

    def __save_document(self, inn, document):
        nalog_user = NalogUser.get_or_create(inn)
        NalogDocumentModel.objects.create(
            user=nalog_user,
            type=document.get('Type', None),
            index=document.get('DocumentIndex', None),
            full_name=document.get('FullName', None),
            address=document.get('Address', None),
            inn=document.get('Inn', None),
            amount=document.get('Amount', None),
            recipient_bank_name=document.get('RecipientBankName', None),
            recipient_bank_bik=document.get('RecipientBankBik', None),
            recipient_bank_account_number=document.get('RecipientBankAccountNumber', None),
            recipient=document.get('Recipient', None),
            recipient_account_number=document.get('RecipientAccountNumber', None),
            recipient_inn=document.get('RecipientInn', None),
            recipient_kpp=document.get('RecipientKpp', None),
            kbk=document.get('Kbk', None),
            oktmo=document.get('Oktmo', None),
            code_101=document.get('Code101', None),
            code_106=document.get('Code106', None),
            code_107=document.get('Code107', None),
            code_110=document.get('Code110', None),
            due_date=document.get('DueDate', None),
            create_time=document.get('CreateTime', None),
            source_id=document.get('SourceId', None)
        )

    def __check_process(self):
        if self.status == NalogRequestModel.StatusChoice.PROCESSING:
            return NalogRequestModel.StatusChoice.PROCESSING

        if self.status == NalogRequestModel.StatusChoice.NOT_FOUND:
            self.request_model.update_status(NalogRequestModel.StatusChoice.NOT_FOUND, self.request_model.response_xml)
            raise MessageIdNotFoundException()

    def __get_request_model(self, message_id):
        self.request_model = NalogRequestModel.get_by_message_id(message_id)

    def __get_message(self):
        response = xmltodict.parse(self.request_model.response_xml)
        self.message, self.status = request_fabric.get_message_response_and_status(response)
