import base64
import hashlib
import hmac
import struct
from io import BytesIO

import numpy as np
import qrcode
import qrcode.image.svg
import requests
import xmltodict
from django.db import transaction
from html2image import Html2Image
from loguru import logger
from lxml import etree

from appcraft_nalog_sdk import request_fabric, settings
from appcraft_nalog_sdk.models import NalogRequestModel, NalogBindPartnerRequestModel, NalogIncomeRequestModel, \
    NalogOfflineKeyModel, NalogUser
from appcraft_nalog_sdk.response_router import ResponseRouter
from giberno.settings import BASE_DIR


class NalogSdk:
    """
    SDK для выполнения запросов в ФНС России
    """

    def __init__(self) -> None:
        super().__init__()
        self.__auth()
        self.base_headers = {
            'SOAPAction': 'urn:SendMessageRequest',
            'FNS-OpenApi-Token': self.auth_token,
            'FNS-OpenApi-UserToken': settings.USER_TOKEN,
            'Content-Type': 'application/xml; charset=utf-8'
        }

    def __auth(self):
        """Получение токена для доступа к API ФНС (AuthRequest)

        """
        request_data = request_fabric.get_auth_request_body(settings.MASTER_TOKEN)
        request_model = NalogRequestModel.create(name='AuthRequest', request_data=request_data)
        result = requests.post(url=settings.AUTH_SERVICE_URL, data=request_data)
        request_model.update_status(NalogRequestModel.StatusChoice.COMPLETED, result.content)
        xml_result = etree.fromstring(result.content)
        self.auth_token = xml_result[0][0][0][0][0][0].text

    def get_status(self, inn: str) -> str:
        """
        Проверка пользователя на статус самозанятого (GetTaxpayerStatusRequest)

        :param inn: инн пользователя
        :return: message_id: идентификатор асинхронного запроса
        """
        request_name = NalogRequestModel.RequestNameChoice.GET_TAXPAYER_STATUS_REQUEST
        request_data = request_fabric.get_taxpayer_status_request(inn)

        return self.__send_request(request_name, request_data, inn)

    def post_bind_partner_with_inn_request(self, inn: str) -> str:
        """
        Привязка пользователя к партнеру

        :param inn: инн пользователя
        :return: message_id: идентификатор асинхронного запроса
        """
        request_name = NalogRequestModel.RequestNameChoice.POST_BIND_PARTNER_WITH_INN_REQUEST
        request_data = request_fabric.post_bind_partner_with_inn_request(inn)

        return self.__send_request(request_name, request_data, inn)

    def get_bind_partner_status_request(self, inn) -> str:
        """
        Проверка статуса заявки на привязку к партнеру

        :param inn: инн пользователя
        :return: message_id: идентификатор асинхронного запроса
        :return: False - ошибка
        """
        bind_request_model = NalogBindPartnerRequestModel.get_bind_request(inn)
        request_name = NalogRequestModel.RequestNameChoice.GET_BIND_PARTNER_STATUS_REQUEST
        request_data = request_fabric.get_bind_partner_status_request(bind_request_model.order_id)

        return self.__send_request(request_name, request_data, inn)

    def post_income_request(self, nalog_request_model: NalogIncomeRequestModel) -> str:
        """
        Регистрация дохода (PostIncomeRequestV2)

        :param nalog_request_model:
        :return: message_id: идентификатор асинхронного запроса
        """
        request_name = NalogRequestModel.RequestNameChoice.POST_INCOME_REQUEST_V2
        request_data = request_fabric.post_income_request(nalog_request_model)

        message_id = self.__send_request(request_name, request_data, nalog_request_model.user.inn)
        nalog_request_model.set_message_id(message_id)
        return message_id

    def post_cancel_receipt_request(self, receipt_id, reason_code) -> str:
        """
        Сторнирование чека (отмена регистрации дохода) (PostCancelReceiptRequestV2)

        :param receipt_id: id чека
        :param reason_code: причина отмены (REFUND, REGISTRATION_MISTAKE)
        :return: message_id: идентификатор асинхронного запроса

        """
        nalog_request_model = NalogIncomeRequestModel.get_by_id(receipt_id)
        nalog_request_model.set_canceled_reason(reason_code)
        request_name = NalogRequestModel.RequestNameChoice.POST_CANCEL_RECEIPT_REQUEST_V2
        request_data = request_fabric.post_cancel_receipt_request(nalog_request_model.user.inn, receipt_id, reason_code)

        return self.__send_request(request_name, request_data, nalog_request_model.user.inn)

    def get_cancel_income_reasons_list_request(self) -> str:
        """
        Получение справочника причин отмены чека (GetCancelIncomeReasonsListRequest)

        :return: message_id: идентификатор асинхронного запроса
        """
        request_name = NalogRequestModel.RequestNameChoice.GET_CANCEL_INCOME_REASONS_LIST_REQUEST
        request_data = request_fabric.get_cancel_income_reasons_list_request()

        return self.__send_request(request_name, request_data)

    def get_granted_permissions_request(self, inn) -> str:
        """
        Получение информации о праве оплаты налогов за самозанятого (GetGrantedPermissionsRequest)

        :param inn: инн пользователя
        :return: message_id: идентификатор асинхронного запроса
        """
        request_name = NalogRequestModel.RequestNameChoice.GET_GRANTED_PERMISSIONS_REQUEST
        request_data = request_fabric.get_granted_permissions_request(inn)

        return self.__send_request(request_name, request_data, inn)

    def post_platform_registration_request(self, name, inn, description, partner_text, link, phone, image) -> str:
        """
        Регистрация приложения партнера (PostPlatformRegistrationRequest)
        :param name:
        :param inn:
        :param description:
        :param partner_text:
        :param link:
        :param phone:
        :param image:
        :return: message_id: идентификатор асинхронного запроса
        """
        request_name = NalogRequestModel.RequestNameChoice.POST_PLATFORM_REGISTRATION_REQUEST
        request_data = request_fabric.post_platform_registration_request(name, inn, description, partner_text, link,
                                                                         phone, image)
        return self.__send_request(request_name, request_data)

    def get_notifications(self, inn) -> str:
        """
        Получение уведомлений для пользователя по инн (GetNotificationsRequest)

        :param inn:  инн пользователя
        :return: message_id: идентификатор асинхронного запроса
        """
        request_name = NalogRequestModel.RequestNameChoice.GET_NOTIFICATIONS_REQUEST
        request_data = request_fabric.get_notifications_request(inn)

        return self.__send_request(request_name, request_data, inn)

    def read_notifications(self, inn, notification_ids) -> str:
        """
        Изменение статуса сообщений на прочитано (PostNotificationsAckRequest)

        :param inn:  инн пользователя
        :param notification_ids  id сообщений (из ФНС), которые необходимо прочесть
        :return: message_id: идентификатор асинхронного запроса
        """

        request_name = NalogRequestModel.RequestNameChoice.POST_NOTIFICATIONS_ACK_REQUEST
        request_data = request_fabric.post_notifications_ack_request(notification_ids)

        return self.__send_request(request_name, request_data, inn)

    def get_newly_unbound_taxpayers_request(self, from_date, to_date, offset):
        """
        Получение фактов отвязазки самозанятых от партнера

        :param from_date: с какого числа/времени
        :param to_date: до какого числа/времени
        :param offset: смещение (лимит на странце = 100)
        :return: message_id: идентификатор асинхронного запроса
        """
        request_name = NalogRequestModel.RequestNameChoice.GET_NEWLY_UNBOUND_TAXPAYERS_REQUEST
        request_data = request_fabric.get_newly_unbound_taxpayers_request(from_date, to_date, offset)

        return self.__send_request(request_name, request_data)

    def get_income_request(self, inn, from_date, to_date):
        """
        Получение информации о зарегистрированных доходах (чтобы проверять статус чека)

        :param inn: инн пользователя
        :param from_date: с какого числа/времени
        :param to_date: до какого числа/времени
        :return: message_id: идентификатор асинхронного запроса
        """
        request_name = NalogRequestModel.RequestNameChoice.GET_INCOME_REQUEST_V2
        request_data = request_fabric.get_income_request(inn, from_date, to_date)

        return self.__send_request(request_name, request_data, inn)

    def get_payment_documents_request(self, inn_list):
        """
        Получение платежных документов

        :param inn_list: список инн
        :return: message_id: идентификатор асинхронного запроса
        """
        request_name = NalogRequestModel.RequestNameChoice.GET_PAYMENT_DOCUMENTS_REQUEST
        request_data = request_fabric.get_payment_documents_request(inn_list)

        return self.__send_request(request_name, request_data)

    def get_keys_request(self, inn_list):
        """
        Получение ключей для формирований чеков в режиме оффлайн

        :param inn_list: список инн
        :return: message_id: идентификатор асинхронного запроса
        """
        request_name = NalogRequestModel.RequestNameChoice.GET_KEYS_REQUEST
        request_data = request_fabric.get_keys_request(inn_list)

        return self.__send_request(request_name, request_data)

    def update_keys(self):
        NalogOfflineKeyModel.delete_all_expired_unused_keys()
        inn_list = NalogUser.get_inn_with_no_keys()
        if inn_list:
            self.get_keys_request(inn_list)

    @staticmethod
    def generate_qrcode(link):
        factory = qrcode.image.svg.SvgPathImage
        qr = qrcode.QRCode(
            version=4,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
            image_factory=factory
        )
        qr.add_data(link)
        qr.make(fit=True)
        img = qr.make_image()  # fill_color="black", back_color="white"
        stream = BytesIO()
        img.save(stream)
        result = stream.getvalue().decode()
        return result

    @classmethod
    def generate_receipt_image(cls, receipt: NalogIncomeRequestModel):
        svg_qr_code = cls.generate_qrcode(receipt.link)

        css = """div{font-family: monospace; font-size: 18px; min-height: 50px; color: #5c6882; } 
        .container{background:white; width: 330px; height: auto; min-height: 630px; padding: 30px; display: flex; 
        flex-flow: column; 
        justify-content: center; align-items: center; } .border-bottom{border-bottom: 1px solid #5c6882; } 
        .flex-row{display: flex; flex-flow: row; } .flex-column{display: flex; flex-flow: column; } 
        .justify-between{justify-content: space-between; } .justify-center{justify-content: center; } 
        .w100{width: 100%; } .w50{width: 50%; } .justify-start{justify-content: 	flex-start; } 
        .justify-end{justify-content: 	flex-end; } .align-start{align-items	: flex-start; } 
        .align-center{align-items	: center; } .align-end{align-items: 	flex-end; } .flex{display: flex; } 
        .header{font-weight: 600; font-size: 22px; } .smz{font-size: 20px; } .bold{font-weight: 600; } 
        .total{font-size: 20px; font-weight: 600; } .h300p{height: 200px; }"""

        html = f'''<div class="container"><div class="border-bottom w100">
        <div class="header">Чек №{receipt.receipt_id}</div> <div class="flex-row w100 justify-between">
        <div class="date">{receipt.operation_time.strftime('%d.%m.%Y')}</div>
        <div class="time">{receipt.operation_time.strftime('%H:%M')}({receipt.operation_time.strftime('%z')})</div>
        </div></div><div class="border-bottom w100 smz flex align-center"> 
        {receipt.user.second_name} {receipt.user.first_name} {receipt.user.patronymic}</div>
        <div class="border-bottom w100 flex-row"> <div class="flex-column w50 align-start">
        <p class="bold">Наименование</p><div>{receipt.name}</div></div><div class="flex-column w50 align-end">
        <p class="bold">Сумма</p> <div>{receipt.amount}</div></div></div>
        <div class="border-bottom w100 flex-row justify-between total"><div class="flex align-center">Итого:</div>
        <div class="flex align-center">{receipt.amount}</div> </div> <div class="border-bottom w100 flex-column">
        <div class="w100 flex justify-between"> <div class="flex align-center">Режим НО</div>
        <div class="flex align-center">НПД</div> </div> <div class="w100 flex justify-between">
        <div class="flex align-center">ИНН</div> <div class="flex align-center">{receipt.user.inn}</div></div></div>
        <div class="border-bottom w100 flex-column"> <div class="w100 flex justify-between">
        <div class="flex align-center">Чек сформировал</div> <div class="flex align-center">Гиберно</div></div>
        <div class="w100 flex justify-between"> <div class="flex align-center">ИНН</div>
        <div class="flex align-center">{settings.PARTNER_INN}</div></div></div>
        <div class="w100 flex justify-center align-center h300p">{svg_qr_code}</div></div>'''

        hti = Html2Image(
            output_path=f'{BASE_DIR}/files/media/receipts/'
        )
        hti.screenshot(html_str=html, css_str=css, size=(410, 900), save_as=f'{receipt.receipt_id}.png')

        receipt.set_receipt_image()

        return receipt.receipt_image

    def make_offline_link(self, inn, amount, operation_time, request_time):
        # Получаем оффлайновый ключ
        offline_key = NalogOfflineKeyModel.get_unused_key(inn)
        if not offline_key:
            return None, None, None

        source_device_id = '0'
        buyer_inn = '0'

        partner_code = settings.PARTNER_ID

        key = base64.b64decode(offline_key.base64_key)
        seq_number = np.base_repr(offline_key.sequence_number, 36).zfill(4)

        mac = hmac.new(
            key,
            digestmod=hashlib.sha256
        )

        mac.update(inn.encode('utf8'))
        mac.update(struct.pack('>Q', int(request_time.timestamp())))
        mac.update(struct.pack('>Q', int(operation_time.timestamp())))
        mac.update(buyer_inn.encode('utf8'))

        amount = int(str(amount).replace('.', ''))
        bytes_amount = amount.to_bytes((amount.bit_length() + 7) // 8, 'big') or b'\0'
        mac.update(bytes_amount)

        mac.update(partner_code.encode('utf8'))
        mac.update(source_device_id.encode('utf8'))

        digest = mac.hexdigest()

        full_hash = np.base_repr(int(digest, 16), 36).lower()
        receipt_hash = full_hash[- 6:]

        offline_key.set_is_used()

        receipt_id = f'{seq_number}{receipt_hash}'

        return f'{settings.INCOME_RECEIPT_URL}/{inn}/{receipt_id}/print', receipt_id, receipt_hash

    def update_processing_statuses(self):
        for request in NalogRequestModel.get_processing_requests():
            logger.debug(request)
            with transaction.atomic():
                message_request = self.__get_message_request(request.message_id)
                logger.debug(message_request)
                message = xmltodict.parse(message_request)
                _, status = request_fabric.get_message_response_and_status(message)
                request.update_status(status, message_request)
                if status == NalogRequestModel.StatusChoice.COMPLETED:
                    self.__save_result(request.message_id)

    def __get_message_request(self, message_id):
        request_data = request_fabric.get_message_body(message_id)

        return requests.post(
            url=settings.SMZ_INTEGRATION_SERVICE_URL,
            headers={
                'SOAPAction': 'urn:GetMessageRequest',
                'FNS-OpenApi-Token': self.auth_token,
                'FNS-OpenApi-UserToken': settings.USER_TOKEN,
                'Content-Type': 'application/xml; charset=utf-8'
            },
            data=request_data
        ).text

    def __save_result(self, message_id):
        """
        Сохранение результата асинхронного запроса

        :param message_id: message id запроса
        """
        router = ResponseRouter(message_id, self)
        return router.route()

    def __send_request(self, method, data, inn=None) -> str:
        """
        Формирование и отправка запроса в ФНС

        :param method: название ФНС метода
        :param data: строка с XML данными для запроса
        :param inn: инн, если запрос совершается над пользователем
        :return: message_id
        :rtype: str
        """
        request_model = NalogRequestModel.create(name=method, request_data=data, inn=inn)

        response = requests.post(
            url=settings.SMZ_INTEGRATION_SERVICE_URL,
            headers=self.base_headers,
            data=data.encode('UTF-8')
        )

        message_id = xmltodict.parse(response.text)['soap:Envelope']['soap:Body']['SendMessageResponse']['MessageId']
        request_model.update_message_id(message_id)

        return message_id
