import base64
import hashlib
import hmac
import struct

import numpy as np
import qrcode
import qrcode.image.svg
from html2image import Html2Image
import requests
import xmltodict
from django.db import transaction
from loguru import logger
from lxml import etree

from appcraft_nalog_sdk import request_fabric, settings
from appcraft_nalog_sdk.models import NalogRequestModel, NalogBindPartnerRequestModel, NalogIncomeRequestModel, \
    NalogOfflineKeyModel, NalogUser
from appcraft_nalog_sdk.response_router import ResponseRouter


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

    @staticmethod
    def generate_receipt_image():
        hti = Html2Image()
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
        html = f"""<div class="container">
		<div class="border-bottom w100">
			<div class="header">Чек № 832748238</div>
			<div class="flex-row w100 justify-between">
				<div class="date">16.09.21</div>
				<div class="time">13:25(+03:00)</div>
			</div>
		</div>
		<div class="border-bottom w100 smz flex align-center">
			Шмелев Сергей Викторович
		</div>
		<div class="border-bottom w100 flex-row">
			<div class="flex-column w50 align-start">
				<p class="bold">Наименование</p>
				<div>Работа 1</div>
			</div>
			<div class="flex-column w50 align-end">
				<p class="bold">Сумма</p>
				<div>1500</div>
			</div>
		</div>
		<div class="border-bottom w100 flex-row justify-between total">
			<div class="flex align-center">Итого:</div>
			<div class="flex align-center">1500</div>
			
		</div>
		<div class="border-bottom w100 flex-column">
			<div class="w100 flex justify-between">
				<div class="flex align-center">Режим НО</div>
				<div class="flex align-center">НПД</div>
			</div>
			<div class="w100 flex justify-between">
				<div class="flex align-center">ИНН</div>
				<div class="flex align-center">67237612661827</div>
			</div>
		</div>
		<div class="border-bottom w100 flex-column">
			<div class="w100 flex justify-between">
				<div class="flex align-center">Чек сформировал</div>
				<div class="flex align-center">Гиберно</div>
			</div>
			<div class="w100 flex justify-between">
				<div class="flex align-center">ИНН</div>
				<div class="flex align-center">2662871791280</div>
			</div>
		</div>
		<div class="w100 flex justify-center align-center h300p">
			<svg width="41mm" height="41mm" version="1.1" viewBox="0 0 41 41" xmlns="http://www.w3.org/2000/svg"><path d="M 35 10 L 35 11 L 36 11 L 36 10 z M 10 32 L 10 33 L 11 33 L 11 32 z M 25 32 L 25 33 L 26 33 L 26 32 z M 23 8 L 23 9 L 24 9 L 24 8 z M 21 24 L 21 25 L 22 25 L 22 24 z M 24 11 L 24 12 L 25 12 L 25 11 z M 27 30 L 27 31 L 28 31 L 28 30 z M 12 9 L 12 10 L 13 10 L 13 9 z M 36 6 L 36 7 L 37 7 L 37 6 z M 17 36 L 17 37 L 18 37 L 18 36 z M 18 35 L 18 36 L 19 36 L 19 35 z M 14 11 L 14 12 L 15 12 L 15 11 z M 4 21 L 4 22 L 5 22 L 5 21 z M 28 18 L 28 19 L 29 19 L 29 18 z M 18 5 L 18 6 L 19 6 L 19 5 z M 29 19 L 29 20 L 30 20 L 30 19 z M 19 8 L 19 9 L 20 9 L 20 8 z M 17 24 L 17 25 L 18 25 L 18 24 z M 7 6 L 7 7 L 8 7 L 8 6 z M 34 18 L 34 19 L 35 19 L 35 18 z M 32 14 L 32 15 L 33 15 L 33 14 z M 35 19 L 35 20 L 36 20 L 36 19 z M 33 15 L 33 16 L 34 16 L 34 15 z M 20 4 L 20 5 L 21 5 L 21 4 z M 32 36 L 32 37 L 33 37 L 33 36 z M 11 26 L 11 27 L 12 27 L 12 26 z M 24 18 L 24 19 L 25 19 L 25 18 z M 13 13 L 13 14 L 14 14 L 14 13 z M 14 18 L 14 19 L 15 19 L 15 18 z M 12 22 L 12 23 L 13 23 L 13 22 z M 15 19 L 15 20 L 16 20 L 16 19 z M 28 25 L 28 26 L 29 26 L 29 25 z M 18 12 L 18 13 L 19 13 L 19 12 z M 29 20 L 29 21 L 30 21 L 30 20 z M 6 22 L 6 23 L 7 23 L 7 22 z M 7 15 L 7 16 L 8 16 L 8 15 z M 31 10 L 31 11 L 32 11 L 32 10 z M 5 19 L 5 20 L 6 20 L 6 19 z M 6 16 L 6 17 L 7 17 L 7 16 z M 33 8 L 33 9 L 34 9 L 34 8 z M 20 11 L 20 12 L 21 12 L 21 11 z M 10 18 L 10 19 L 11 19 L 11 18 z M 23 22 L 23 23 L 24 23 L 24 22 z M 24 25 L 24 26 L 25 26 L 25 25 z M 20 33 L 20 34 L 21 34 L 21 33 z M 10 36 L 10 37 L 11 37 L 11 36 z M 25 12 L 25 13 L 26 13 L 26 12 z M 21 28 L 21 29 L 22 29 L 22 28 z M 26 11 L 26 12 L 27 12 L 27 11 z M 22 35 L 22 36 L 23 36 L 23 35 z M 14 13 L 14 14 L 15 14 L 15 13 z M 12 29 L 12 30 L 13 30 L 13 29 z M 15 8 L 15 9 L 16 9 L 16 8 z M 28 32 L 28 33 L 29 33 L 29 32 z M 16 11 L 16 12 L 17 12 L 17 11 z M 14 23 L 14 24 L 15 24 L 15 23 z M 19 14 L 19 15 L 20 15 L 20 14 z M 15 30 L 15 31 L 16 31 L 16 30 z M 30 34 L 30 35 L 31 35 L 31 34 z M 4 9 L 4 10 L 5 10 L 5 9 z M 28 6 L 28 7 L 29 7 L 29 6 z M 16 33 L 16 34 L 17 34 L 17 33 z M 31 35 L 31 36 L 32 36 L 32 35 z M 5 4 L 5 5 L 6 5 L 6 4 z M 8 15 L 8 16 L 9 16 L 9 15 z M 32 28 L 32 29 L 33 29 L 33 28 z M 33 33 L 33 34 L 34 34 L 34 33 z M 10 5 L 10 6 L 11 6 L 11 5 z M 34 6 L 34 7 L 35 7 L 35 6 z M 35 31 L 35 32 L 36 32 L 36 31 z M 24 32 L 24 33 L 25 33 L 25 32 z M 20 24 L 20 25 L 21 25 L 21 24 z M 10 31 L 10 32 L 11 32 L 11 31 z M 25 21 L 25 22 L 26 22 L 26 21 z M 21 21 L 21 22 L 22 22 L 22 21 z M 36 27 L 36 28 L 37 28 L 37 27 z M 26 34 L 26 35 L 27 35 L 27 34 z M 22 26 L 22 27 L 23 27 L 23 26 z M 12 4 L 12 5 L 13 5 L 13 4 z M 36 17 L 36 18 L 37 18 L 37 17 z M 13 33 L 13 34 L 14 34 L 14 33 z M 14 30 L 14 31 L 15 31 L 15 30 z M 4 32 L 4 33 L 5 33 L 5 32 z M 16 24 L 16 25 L 17 25 L 17 24 z M 31 24 L 31 25 L 32 25 L 32 24 z M 17 29 L 17 30 L 18 30 L 18 29 z M 32 27 L 32 28 L 33 28 L 33 27 z M 6 34 L 6 35 L 7 35 L 7 34 z M 30 7 L 30 8 L 31 8 L 31 7 z M 33 26 L 33 27 L 34 27 L 34 26 z M 32 17 L 32 18 L 33 18 L 33 17 z M 35 4 L 35 5 L 36 5 L 36 4 z M 31 36 L 31 37 L 32 37 L 32 36 z M 10 22 L 10 23 L 11 23 L 11 22 z M 26 21 L 26 22 L 27 22 L 27 21 z M 24 5 L 24 6 L 25 6 L 25 5 z M 22 21 L 22 22 L 23 22 L 23 21 z M 27 24 L 27 25 L 28 25 L 28 24 z M 25 8 L 25 9 L 26 9 L 26 8 z M 12 11 L 12 12 L 13 12 L 13 11 z M 36 8 L 36 9 L 37 9 L 37 8 z M 18 11 L 18 12 L 19 12 L 19 11 z M 4 13 L 4 14 L 5 14 L 5 13 z M 7 8 L 7 9 L 8 9 L 8 8 z M 32 8 L 32 9 L 33 9 L 33 8 z M 9 10 L 9 11 L 10 11 L 10 10 z M 20 6 L 20 7 L 21 7 L 21 6 z M 34 26 L 34 27 L 35 27 L 35 26 z M 23 19 L 23 20 L 24 20 L 24 19 z M 35 27 L 35 28 L 36 28 L 36 27 z M 9 36 L 9 37 L 10 37 L 10 36 z M 22 12 L 22 13 L 23 13 L 23 12 z M 12 18 L 12 19 L 13 19 L 13 18 z M 26 6 L 26 7 L 27 7 L 27 6 z M 13 19 L 13 20 L 14 20 L 14 19 z M 28 27 L 28 28 L 29 28 L 29 27 z M 18 18 L 18 19 L 19 19 L 19 18 z M 14 26 L 14 27 L 15 27 L 15 26 z M 29 26 L 29 27 L 30 27 L 30 26 z M 19 19 L 19 20 L 20 20 L 20 19 z M 17 15 L 17 16 L 18 16 L 18 15 z M 4 4 L 4 5 L 5 5 L 5 4 z M 7 17 L 7 18 L 8 18 L 8 17 z M 31 28 L 31 29 L 32 29 L 32 28 z M 32 7 L 32 8 L 33 8 L 33 7 z M 6 14 L 6 15 L 7 15 L 7 14 z M 33 6 L 33 7 L 34 7 L 34 6 z M 7 23 L 7 24 L 8 24 L 8 23 z M 10 16 L 10 17 L 11 17 L 11 16 z M 8 24 L 8 25 L 9 25 L 9 24 z M 23 24 L 23 25 L 24 25 L 24 24 z M 21 8 L 21 9 L 22 9 L 22 8 z M 35 32 L 35 33 L 36 33 L 36 32 z M 24 27 L 24 28 L 25 28 L 25 27 z M 22 7 L 22 8 L 23 8 L 23 7 z M 20 35 L 20 36 L 21 36 L 21 35 z M 25 26 L 25 27 L 26 27 L 26 26 z M 21 34 L 21 35 L 22 35 L 22 34 z M 36 22 L 36 23 L 37 23 L 37 22 z M 27 4 L 27 5 L 28 5 L 28 4 z M 12 31 L 12 32 L 13 32 L 13 31 z M 36 12 L 36 13 L 37 13 L 37 12 z M 13 30 L 13 31 L 14 31 L 14 30 z M 28 34 L 28 35 L 29 35 L 29 34 z M 18 21 L 18 22 L 19 22 L 19 21 z M 16 5 L 16 6 L 17 6 L 17 5 z M 29 35 L 29 36 L 30 36 L 30 35 z M 19 24 L 19 25 L 20 25 L 20 24 z M 17 8 L 17 9 L 18 9 L 18 8 z M 15 32 L 15 33 L 16 33 L 16 32 z M 30 32 L 30 33 L 31 33 L 31 32 z M 16 35 L 16 36 L 17 36 L 17 35 z M 5 10 L 5 11 L 6 11 L 6 10 z M 17 34 L 17 35 L 18 35 L 18 34 z M 32 30 L 32 31 L 33 31 L 33 30 z M 30 10 L 30 11 L 31 11 L 31 10 z M 9 12 L 9 13 L 10 13 L 10 12 z M 34 4 L 34 5 L 35 5 L 35 4 z M 8 23 L 8 24 L 9 24 L 9 23 z M 9 22 L 9 23 L 10 23 L 10 22 z M 24 34 L 24 35 L 25 35 L 25 34 z M 20 26 L 20 27 L 21 27 L 21 26 z M 27 29 L 27 30 L 28 30 L 28 29 z M 18 28 L 18 29 L 19 29 L 19 28 z M 14 28 L 14 29 L 15 29 L 15 28 z M 4 34 L 4 35 L 5 35 L 5 34 z M 18 6 L 18 7 L 19 7 L 19 6 z M 16 26 L 16 27 L 17 27 L 17 26 z M 31 26 L 31 27 L 32 27 L 32 26 z M 6 32 L 6 33 L 7 33 L 7 32 z M 30 5 L 30 6 L 31 6 L 31 5 z M 31 16 L 31 17 L 32 17 L 32 16 z M 8 30 L 8 31 L 9 31 L 9 30 z M 32 19 L 32 20 L 33 20 L 33 19 z M 33 18 L 33 19 L 34 19 L 34 18 z M 20 17 L 20 18 L 21 18 L 21 17 z M 10 20 L 10 21 L 11 21 L 11 20 z M 25 28 L 25 29 L 26 29 L 26 28 z M 8 36 L 8 37 L 9 37 L 9 36 z M 21 12 L 21 13 L 22 13 L 22 12 z M 11 25 L 11 26 L 12 26 L 12 25 z M 26 27 L 26 28 L 27 28 L 27 27 z M 36 36 L 36 37 L 37 37 L 37 36 z M 22 19 L 22 20 L 23 20 L 23 19 z M 12 13 L 12 14 L 13 14 L 13 13 z M 36 10 L 36 11 L 37 11 L 37 10 z M 26 13 L 26 14 L 27 14 L 27 13 z M 13 8 L 13 9 L 14 9 L 14 8 z M 27 16 L 27 17 L 28 17 L 28 16 z M 14 7 L 14 8 L 15 8 L 15 7 z M 19 30 L 19 31 L 20 31 L 20 30 z M 15 14 L 15 15 L 16 15 L 16 14 z M 16 17 L 16 18 L 17 18 L 17 17 z M 5 20 L 5 21 L 6 21 L 6 20 z M 19 4 L 19 5 L 20 5 L 20 4 z M 17 20 L 17 21 L 18 21 L 18 20 z M 6 27 L 6 28 L 7 28 L 7 27 z M 30 12 L 30 13 L 31 13 L 31 12 z M 7 10 L 7 11 L 8 11 L 8 10 z M 5 14 L 5 15 L 6 15 L 6 14 z M 32 10 L 32 11 L 33 11 L 33 10 z M 35 15 L 35 16 L 36 16 L 36 15 z M 21 5 L 21 6 L 22 6 L 22 5 z M 11 22 L 11 23 L 12 23 L 12 22 z M 22 10 L 22 11 L 23 11 L 23 10 z M 25 15 L 25 16 L 26 16 L 26 15 z M 14 36 L 14 37 L 15 37 L 15 36 z M 21 31 L 21 32 L 22 32 L 22 31 z M 22 36 L 22 37 L 23 37 L 23 36 z M 27 9 L 27 10 L 28 10 L 28 9 z M 28 29 L 28 30 L 29 30 L 29 29 z M 17 13 L 17 14 L 18 14 L 18 13 z M 30 23 L 30 24 L 31 24 L 31 23 z M 4 6 L 4 7 L 5 7 L 5 6 z M 6 12 L 6 13 L 7 13 L 7 12 z M 9 17 L 9 18 L 10 18 L 10 17 z M 33 4 L 33 5 L 34 5 L 34 4 z M 29 36 L 29 37 L 30 37 L 30 36 z M 10 6 L 10 7 L 11 7 L 11 6 z M 34 35 L 34 36 L 35 36 L 35 35 z M 11 15 L 11 16 L 12 16 L 12 15 z M 35 34 L 35 35 L 36 35 L 36 34 z M 9 27 L 9 28 L 10 28 L 10 27 z M 22 5 L 22 6 L 23 6 L 23 5 z M 25 24 L 25 25 L 26 25 L 26 24 z M 21 32 L 21 33 L 22 33 L 22 32 z M 27 6 L 27 7 L 28 7 L 28 6 z M 36 14 L 36 15 L 37 15 L 37 14 z M 18 27 L 18 28 L 19 28 L 19 27 z M 14 35 L 14 36 L 15 36 L 15 35 z M 30 30 L 30 31 L 31 31 L 31 30 z M 28 10 L 28 11 L 29 11 L 29 10 z M 17 32 L 17 33 L 18 33 L 18 32 z M 32 24 L 32 25 L 33 25 L 33 24 z M 6 7 L 6 8 L 7 8 L 7 7 z M 30 8 L 30 9 L 31 9 L 31 8 z M 7 30 L 7 31 L 8 31 L 8 30 z M 10 9 L 10 10 L 11 10 L 11 9 z M 34 10 L 34 11 L 35 11 L 35 10 z M 8 33 L 8 34 L 9 34 L 9 33 z M 23 35 L 23 36 L 24 36 L 24 35 z M 9 20 L 9 21 L 10 21 L 10 20 z M 7 36 L 7 37 L 8 37 L 8 36 z M 10 35 L 10 36 L 11 36 L 11 35 z M 23 9 L 23 10 L 24 10 L 24 9 z M 24 10 L 24 11 L 25 11 L 25 10 z M 12 8 L 12 9 L 13 9 L 13 8 z M 36 5 L 36 6 L 37 6 L 37 5 z M 13 5 L 13 6 L 14 6 L 14 5 z M 18 34 L 18 35 L 19 35 L 19 34 z M 14 10 L 14 11 L 15 11 L 15 10 z M 19 35 L 19 36 L 20 36 L 20 35 z M 15 27 L 15 28 L 16 28 L 16 27 z M 4 20 L 4 21 L 5 21 L 5 20 z M 28 17 L 28 18 L 29 18 L 29 17 z M 29 12 L 29 13 L 30 13 L 30 12 z M 19 9 L 19 10 L 20 10 L 20 9 z M 6 30 L 6 31 L 7 31 L 7 30 z M 7 7 L 7 8 L 8 8 L 8 7 z M 31 18 L 31 19 L 32 19 L 32 18 z M 8 8 L 8 9 L 9 9 L 9 8 z M 33 16 L 33 17 L 34 17 L 34 16 z M 20 19 L 20 20 L 21 20 L 21 19 z M 10 26 L 10 27 L 11 27 L 11 26 z M 23 14 L 23 15 L 24 15 L 24 14 z M 21 18 L 21 19 L 22 19 L 22 18 z M 24 17 L 24 18 L 25 18 L 25 17 z M 13 36 L 13 37 L 14 37 L 14 36 z M 21 36 L 21 37 L 22 37 L 22 36 z M 36 28 L 36 29 L 37 29 L 37 28 z M 26 19 L 26 20 L 27 20 L 27 19 z M 14 5 L 14 6 L 15 6 L 15 5 z M 12 21 L 12 22 L 13 22 L 13 21 z M 15 16 L 15 17 L 16 17 L 16 16 z M 28 24 L 28 25 L 29 25 L 29 24 z M 16 19 L 16 20 L 17 20 L 17 19 z M 5 26 L 5 27 L 6 27 L 6 26 z M 29 21 L 29 22 L 30 22 L 30 21 z M 19 6 L 19 7 L 20 7 L 20 6 z M 17 18 L 17 19 L 18 19 L 18 18 z M 6 25 L 6 26 L 7 26 L 7 25 z M 30 26 L 30 27 L 31 27 L 31 26 z M 5 12 L 5 13 L 6 13 L 6 12 z M 8 7 L 8 8 L 9 8 L 9 7 z M 32 4 L 32 5 L 33 5 L 33 4 z M 6 19 L 6 20 L 7 20 L 7 19 z M 20 10 L 20 11 L 21 11 L 21 10 z M 34 30 L 34 31 L 35 31 L 35 30 z M 35 23 L 35 24 L 36 24 L 36 23 z M 24 24 L 24 25 L 25 25 L 25 24 z M 22 8 L 22 9 L 23 9 L 23 8 z M 20 32 L 20 33 L 21 33 L 21 32 z M 25 13 L 25 14 L 26 14 L 26 13 z M 21 29 L 21 30 L 22 30 L 22 29 z M 26 10 L 26 11 L 27 11 L 27 10 z M 22 34 L 22 35 L 23 35 L 23 34 z M 27 11 L 27 12 L 28 12 L 28 11 z M 14 12 L 14 13 L 15 13 L 15 12 z M 15 9 L 15 10 L 16 10 L 16 9 z M 13 25 L 13 26 L 14 26 L 14 25 z M 28 31 L 28 32 L 29 32 L 29 31 z M 16 10 L 16 11 L 17 11 L 17 10 z M 14 22 L 14 23 L 15 23 L 15 22 z M 4 8 L 4 9 L 5 9 L 5 8 z M 28 5 L 28 6 L 29 6 L 29 5 z M 16 32 L 16 33 L 17 33 L 17 32 z M 31 32 L 31 33 L 32 33 L 32 32 z M 8 14 L 8 15 L 9 15 L 9 14 z M 6 10 L 6 11 L 7 11 L 7 10 z M 9 15 L 9 16 L 10 16 L 10 15 z M 33 34 L 33 35 L 34 35 L 34 34 z M 10 4 L 10 5 L 11 5 L 11 4 z M 34 33 L 34 34 L 35 34 L 35 33 z M 8 20 L 8 21 L 9 21 L 9 20 z M 6 36 L 6 37 L 7 37 L 7 36 z M 35 28 L 35 29 L 36 29 L 36 28 z M 10 30 L 10 31 L 11 31 L 11 30 z M 36 26 L 36 27 L 37 27 L 37 26 z M 26 29 L 26 30 L 27 30 L 27 29 z M 22 29 L 22 30 L 23 30 L 23 29 z M 27 32 L 27 33 L 28 33 L 28 32 z M 12 35 L 12 36 L 13 36 L 13 35 z M 36 16 L 36 17 L 37 17 L 37 16 z M 13 34 L 13 35 L 14 35 L 14 34 z M 30 28 L 30 29 L 31 29 L 31 28 z M 4 31 L 4 32 L 5 32 L 5 31 z M 31 25 L 31 26 L 32 26 L 32 25 z M 5 30 L 5 31 L 6 31 L 6 30 z M 30 6 L 30 7 L 31 7 L 31 6 z M 33 27 L 33 28 L 34 28 L 34 27 z M 7 32 L 7 33 L 8 33 L 8 32 z M 34 8 L 34 9 L 35 9 L 35 8 z M 32 16 L 32 17 L 33 17 L 33 16 z M 10 33 L 10 34 L 11 34 L 11 33 z M 25 31 L 25 32 L 26 32 L 26 31 z M 23 11 L 23 12 L 24 12 L 24 11 z M 21 15 L 21 16 L 22 16 L 22 15 z M 12 36 L 12 37 L 13 37 L 13 36 z M 26 20 L 26 21 L 27 21 L 27 20 z M 24 4 L 24 5 L 25 5 L 25 4 z M 22 20 L 22 21 L 23 21 L 23 20 z M 12 10 L 12 11 L 13 11 L 13 10 z M 36 7 L 36 8 L 37 8 L 37 7 z M 14 8 L 14 9 L 15 9 L 15 8 z M 28 19 L 28 20 L 29 20 L 29 19 z M 18 10 L 18 11 L 19 11 L 19 10 z M 29 18 L 29 19 L 30 19 L 30 18 z M 19 11 L 19 12 L 20 12 L 20 11 z M 17 23 L 17 24 L 18 24 L 18 23 z M 6 28 L 6 29 L 7 29 L 7 28 z M 4 12 L 4 13 L 5 13 L 5 12 z M 33 20 L 33 21 L 34 21 L 34 20 z M 31 4 L 31 5 L 32 5 L 32 4 z M 8 10 L 8 11 L 9 11 L 9 10 z M 33 14 L 33 15 L 34 15 L 34 14 z M 20 5 L 20 6 L 21 6 L 21 5 z M 10 24 L 10 25 L 11 25 L 11 24 z M 23 16 L 23 17 L 24 17 L 24 16 z M 21 16 L 21 17 L 22 17 L 22 16 z M 24 19 L 24 20 L 25 20 L 25 19 z M 27 22 L 27 23 L 28 23 L 28 22 z M 25 18 L 25 19 L 26 19 L 26 18 z M 12 17 L 12 18 L 13 18 L 13 17 z M 36 30 L 36 31 L 37 31 L 37 30 z M 13 12 L 13 13 L 14 13 L 14 12 z M 14 19 L 14 20 L 15 20 L 15 19 z M 13 22 L 13 23 L 14 23 L 14 22 z M 28 26 L 28 27 L 29 27 L 29 26 z M 18 13 L 18 14 L 19 14 L 19 13 z M 5 24 L 5 25 L 6 25 L 6 24 z M 29 27 L 29 28 L 30 28 L 30 27 z M 19 16 L 19 17 L 20 17 L 20 16 z M 17 16 L 17 17 L 18 17 L 18 16 z M 6 23 L 6 24 L 7 24 L 7 23 z M 8 17 L 8 18 L 9 18 L 9 17 z M 32 6 L 32 7 L 33 7 L 33 6 z M 6 17 L 6 18 L 7 18 L 7 17 z M 9 4 L 9 5 L 10 5 L 10 4 z M 33 7 L 33 8 L 34 8 L 34 7 z M 7 20 L 7 21 L 8 21 L 8 20 z M 5 36 L 5 37 L 6 37 L 6 36 z M 11 18 L 11 19 L 12 19 L 12 18 z M 24 26 L 24 27 L 25 27 L 25 26 z M 22 6 L 22 7 L 23 7 L 23 6 z M 20 34 L 20 35 L 21 35 L 21 34 z M 36 21 L 36 22 L 37 22 L 37 21 z M 26 8 L 26 9 L 27 9 L 27 8 z M 15 11 L 15 12 L 16 12 L 16 11 z M 18 20 L 18 21 L 19 21 L 19 20 z M 16 4 L 16 5 L 17 5 L 17 4 z M 14 20 L 14 21 L 15 21 L 15 20 z M 29 28 L 29 29 L 30 29 L 30 28 z M 30 35 L 30 36 L 31 36 L 31 35 z M 4 10 L 4 11 L 5 11 L 5 10 z M 16 34 L 16 35 L 17 35 L 17 34 z M 31 34 L 31 35 L 32 35 L 32 34 z M 32 29 L 32 30 L 33 30 L 33 29 z M 6 8 L 6 9 L 7 9 L 7 8 z M 33 32 L 33 33 L 34 33 L 34 32 z M 10 10 L 10 11 L 11 11 L 11 10 z M 34 7 L 34 8 L 35 8 L 35 7 z M 23 30 L 23 31 L 24 31 L 24 30 z M 24 33 L 24 34 L 25 34 L 25 33 z M 20 25 L 20 26 L 21 26 L 21 25 z M 10 28 L 10 29 L 11 29 L 11 28 z M 25 20 L 25 21 L 26 21 L 26 20 z M 23 4 L 23 5 L 24 5 L 24 4 z M 21 20 L 21 21 L 22 21 L 22 20 z M 26 35 L 26 36 L 27 36 L 27 35 z M 22 27 L 22 28 L 23 28 L 23 27 z M 27 34 L 27 35 L 28 35 L 28 34 z M 12 5 L 12 6 L 13 6 L 13 5 z M 36 18 L 36 19 L 37 19 L 37 18 z M 13 32 L 13 33 L 14 33 L 14 32 z M 14 31 L 14 32 L 15 32 L 15 31 z M 19 22 L 19 23 L 20 23 L 20 22 z M 15 22 L 15 23 L 16 23 L 16 22 z M 4 33 L 4 34 L 5 34 L 5 33 z M 16 25 L 16 26 L 17 26 L 17 25 z M 31 27 L 31 28 L 32 28 L 32 27 z M 5 28 L 5 29 L 6 29 L 6 28 z M 17 28 L 17 29 L 18 29 L 18 28 z M 32 20 L 32 21 L 33 21 L 33 20 z M 30 4 L 30 5 L 31 5 L 31 4 z M 33 25 L 33 26 L 34 26 L 34 25 z M 7 34 L 7 35 L 8 35 L 8 34 z M 31 17 L 31 18 L 32 18 L 32 17 z M 34 14 L 34 15 L 35 15 L 35 14 z M 33 19 L 33 20 L 34 20 L 34 19 z M 20 16 L 20 17 L 21 17 L 21 16 z M 25 29 L 25 30 L 26 30 L 26 29 z M 21 13 L 21 14 L 22 14 L 22 13 z M 26 26 L 26 27 L 27 27 L 27 26 z M 24 6 L 24 7 L 25 7 L 25 6 z M 22 18 L 22 19 L 23 19 L 23 18 z M 27 27 L 27 28 L 28 28 L 28 27 z M 12 12 L 12 13 L 13 13 L 13 12 z M 36 9 L 36 10 L 37 10 L 37 9 z M 26 12 L 26 13 L 27 13 L 27 12 z M 14 6 L 14 7 L 15 7 L 15 6 z M 18 8 L 18 9 L 19 9 L 19 8 z M 16 16 L 16 17 L 17 17 L 17 16 z M 17 21 L 17 22 L 18 22 L 18 21 z M 6 26 L 6 27 L 7 27 L 7 26 z M 30 15 L 30 16 L 31 16 L 31 15 z M 8 4 L 8 5 L 9 5 L 9 4 z M 4 36 L 4 37 L 5 37 L 5 36 z M 35 12 L 35 13 L 36 13 L 36 12 z M 10 14 L 10 15 L 11 15 L 11 14 z M 22 13 L 22 14 L 23 14 L 23 13 z M 25 16 L 25 17 L 26 17 L 26 16 z M 26 7 L 26 8 L 27 8 L 27 7 z M 27 14 L 27 15 L 28 15 L 28 14 z M 15 4 L 15 5 L 16 5 L 16 4 z M 28 28 L 28 29 L 29 29 L 29 28 z M 18 19 L 18 20 L 19 20 L 19 19 z M 14 27 L 14 28 L 15 28 L 15 27 z M 6 21 L 6 22 L 7 22 L 7 21 z M 4 5 L 4 6 L 5 6 L 5 5 z M 7 16 L 7 17 L 8 17 L 8 16 z M 5 16 L 5 17 L 6 17 L 6 16 z M 32 32 L 32 33 L 33 33 L 33 32 z M 7 22 L 7 23 L 8 23 L 8 22 z M 23 27 L 23 28 L 24 28 L 24 27 z M 26 36 L 26 37 L 27 37 L 27 36 z M 34 36 L 34 37 L 35 37 L 35 36 z M 36 23 L 36 24 L 37 24 L 37 23 z M 36 13 L 36 14 L 37 14 L 37 13 z M 13 29 L 13 30 L 14 30 L 14 29 z M 18 26 L 18 27 L 19 27 L 19 26 z M 16 6 L 16 7 L 17 7 L 17 6 z M 14 34 L 14 35 L 15 35 L 15 34 z M 19 27 L 19 28 L 20 28 L 20 27 z M 15 35 L 15 36 L 16 36 L 16 35 z M 4 28 L 4 29 L 5 29 L 5 28 z M 32 31 L 32 32 L 33 32 L 33 31 z M 6 6 L 6 7 L 7 7 L 7 6 z M 10 8 L 10 9 L 11 9 L 11 8 z M 8 32 L 8 33 L 9 33 L 9 32 z M 23 32 L 23 33 L 24 33 L 24 32 z M 9 21 L 9 22 L 10 22 L 10 21 z M 24 35 L 24 36 L 25 36 L 25 35 z M 20 27 L 20 28 L 21 28 L 21 27 z M 10 34 L 10 35 L 11 35 L 11 34 z M 25 34 L 25 35 L 26 35 L 26 34 z M 23 6 L 23 7 L 24 7 L 24 6 z M 21 26 L 21 27 L 22 27 L 22 26 z M 36 4 L 36 5 L 37 5 L 37 4 z M 18 29 L 18 30 L 19 30 L 19 29 z M 19 32 L 19 33 L 20 33 L 20 32 z M 15 24 L 15 25 L 16 25 L 16 24 z M 4 35 L 4 36 L 5 36 L 5 35 z M 28 16 L 28 17 L 29 17 L 29 16 z M 18 7 L 18 8 L 19 8 L 19 7 z M 16 27 L 16 28 L 17 28 L 17 27 z M 29 13 L 29 14 L 30 14 L 30 13 z M 17 26 L 17 27 L 18 27 L 18 26 z M 32 22 L 32 23 L 33 23 L 33 22 z M 6 33 L 6 34 L 7 34 L 7 33 z M 30 18 L 30 19 L 31 19 L 31 18 z M 33 23 L 33 24 L 34 24 L 34 23 z M 7 4 L 7 5 L 8 5 L 8 4 z M 31 19 L 31 20 L 32 20 L 32 19 z M 32 12 L 32 13 L 33 13 L 33 12 z M 9 30 L 9 31 L 10 31 L 10 30 z M 33 17 L 33 18 L 34 18 L 34 17 z M 20 18 L 20 19 L 21 19 L 21 18 z M 34 22 L 34 23 L 35 23 L 35 22 z M 24 16 L 24 17 L 25 17 L 25 16 z M 25 5 L 25 6 L 26 6 L 26 5 z M 12 14 L 12 15 L 13 15 L 13 14 z M 26 18 L 26 19 L 27 19 L 27 18 z M 13 15 L 13 16 L 14 16 L 14 15 z M 27 19 L 27 20 L 28 20 L 28 19 z M 4 26 L 4 27 L 5 27 L 5 26 z M 16 18 L 16 19 L 17 19 L 17 18 z M 6 24 L 6 25 L 7 25 L 7 24 z M 4 16 L 4 17 L 5 17 L 5 16 z M 7 13 L 7 14 L 8 14 L 8 13 z M 8 6 L 8 7 L 9 7 L 9 6 z M 35 14 L 35 15 L 36 15 L 36 14 z M 33 10 L 33 11 L 34 11 L 34 10 z M 10 12 L 10 13 L 11 13 L 11 12 z M 25 36 L 25 37 L 26 37 L 26 36 z M 11 17 L 11 18 L 12 18 L 12 17 z M 33 36 L 33 37 L 34 37 L 34 36 z M 22 11 L 22 12 L 23 12 L 23 11 z M 36 34 L 36 35 L 37 35 L 37 34 z M 26 5 L 26 6 L 27 6 L 27 5 z M 13 16 L 13 17 L 14 17 L 14 16 z M 27 8 L 27 9 L 28 9 L 28 8 z M 15 6 L 15 7 L 16 7 L 16 6 z M 13 26 L 13 27 L 14 27 L 14 26 z M 28 30 L 28 31 L 29 31 L 29 30 z M 14 25 L 14 26 L 15 26 L 15 25 z M 17 12 L 17 13 L 18 13 L 18 12 z M 30 20 L 30 21 L 31 21 L 31 20 z M 4 7 L 4 8 L 5 8 L 5 7 z M 28 4 L 28 5 L 29 5 L 29 4 z M 7 18 L 7 19 L 8 19 L 8 18 z M 31 33 L 31 34 L 32 34 L 32 33 z M 8 13 L 8 14 L 9 14 L 9 13 z M 32 34 L 32 35 L 33 35 L 33 34 z M 6 13 L 6 14 L 7 14 L 7 13 z M 9 16 L 9 17 L 10 17 L 10 16 z M 33 35 L 33 36 L 34 36 L 34 35 z M 7 24 L 7 25 L 8 25 L 8 24 z M 10 7 L 10 8 L 11 8 L 11 7 z M 34 32 L 34 33 L 35 33 L 35 32 z M 8 27 L 8 28 L 9 28 L 9 27 z M 35 29 L 35 30 L 36 30 L 36 29 z M 25 23 L 25 24 L 26 24 L 26 23 z M 21 23 L 21 24 L 22 24 L 22 23 z M 36 25 L 36 26 L 37 26 L 37 25 z M 26 28 L 26 29 L 27 29 L 27 28 z M 22 28 L 22 29 L 23 29 L 23 28 z M 27 33 L 27 34 L 28 34 L 28 33 z M 12 34 L 12 35 L 13 35 L 13 34 z M 13 35 L 13 36 L 14 36 L 14 35 z M 29 32 L 29 33 L 30 33 L 30 32 z M 17 5 L 17 6 L 18 6 L 18 5 z M 4 30 L 4 31 L 5 31 L 5 30 z M 28 11 L 28 12 L 29 12 L 29 11 z M 17 31 L 17 32 L 18 32 L 18 31 z M 32 25 L 32 26 L 33 26 L 33 25 z M 6 4 L 6 5 L 7 5 L 7 4 z M 30 9 L 30 10 L 31 10 L 31 9 z M 18 36 L 18 37 L 19 37 L 19 36 z M 33 28 L 33 29 L 34 29 L 34 28 z M 7 33 L 7 34 L 8 34 L 8 33 z M 31 12 L 31 13 L 32 13 L 32 12 z M 8 34 L 8 35 L 9 35 L 9 34 z" id="qr-path" fill="#000000" fill-opacity="1" fill-rule="nonzero" stroke="none"/></svg>
			
		</div>

	</div>"""

        hti.screenshot(html_str=html, css_str=css, save_as='red_page.png', size=(390,900))

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
