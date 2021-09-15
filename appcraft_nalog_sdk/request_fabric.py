import xmltodict

from appcraft_nalog_sdk.decorators import auth_message_request, send_message_request, \
    get_message_by_id
from appcraft_nalog_sdk.models import NalogRequestModel


def get_message_request(request_xml):
    data = xmltodict.parse(request_xml)
    return data['soap-env:Envelope']['soap-env:Body']['ns0:SendMessageRequest']['ns0:Message']


def get_message_response_and_status(response):
    message = None
    status = __get_processing_status(response)

    if status == NalogRequestModel.StatusChoice.COMPLETED:
        message = response['soap:Envelope']['soap:Body']['GetMessageResponse']['Message']

    return message, status


def __get_processing_status(data):
    if 'soap:Fault' in data['soap:Envelope']['soap:Body']:
        return NalogRequestModel.StatusChoice.NOT_FOUND
    return data['soap:Envelope']['soap:Body']['GetMessageResponse']['ProcessingStatus']


@get_message_by_id
def get_message_body(message_id):
    return f'''
<MessageId>{message_id}</MessageId>
'''


@auth_message_request
def get_auth_request_body(token: str):
    return f'''
<tns:AuthRequest xmlns:tns="urn://x-artefacts-gnivc-ru/ais3/kkt/AuthService/types/1.0">
    <tns:AuthAppInfo>
        <tns:MasterToken>{token}</tns:MasterToken>
    </tns:AuthAppInfo>
</tns:AuthRequest>
'''


@send_message_request
def get_taxpayer_status_request(inn: str):
    return f'''
<tns:GetTaxpayerStatusRequest xmlns:tns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
    <tns:Inn>{inn}</tns:Inn>
</tns:GetTaxpayerStatusRequest>
'''


@send_message_request
def get_notifications_request(inn: str):
    return f'''
<GetNotificationsRequest
        xmlns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
        <notificationsRequest>
            <inn>{inn}</inn>
            <GetAcknowleged>true</GetAcknowleged>
            <GetArchived>true</GetArchived>
        </notificationsRequest>
</GetNotificationsRequest>
'''


@send_message_request
def post_notifications_ack_request(ids: list):
    messages_block = ''
    for message_id in ids:
        messages_block += __create_notification_message_id_block(message_id)
    return f'''
<PostNotificationsAckRequest
        xmlns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
        <notificationList>
            <inn>507271600230</inn>
            {messages_block}
        </notificationList>
</PostNotificationsAckRequest>
'''


def __create_notification_message_id_block(message_id):
    return f'<messageId>{message_id}</messageId>\n'


@send_message_request
def post_bind_partner_with_inn_request(inn: str):
    return f'''
<PostBindPartnerWithInnRequest
        xmlns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
    <Inn>{inn}</Inn>
    <Permissions>TAX_PAYMENT</Permissions>
</PostBindPartnerWithInnRequest>
'''


@send_message_request
def get_bind_partner_status_request(order_id):
    return f'''
<GetBindPartnerStatusRequest xmlns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
    <Id>{order_id}</Id>
</GetBindPartnerStatusRequest>
'''


@send_message_request
def post_income_request(nalog_request_model):
    if nalog_request_model.latitude and nalog_request_model.longitude:
        geo_info_block = f'''
            <GeoInfo>
                <Latitude>{nalog_request_model.latitude}</Latitude>
                <Longitude>{nalog_request_model.longitude}</Longitude>
            </GeoInfo>
        '''
    else:
        geo_info_block = ''

    return f'''
<PostIncomeRequestV2 xmlns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
    <Inn>{nalog_request_model.user.inn}</Inn>
    <RequestTime>{nalog_request_model.request_time.isoformat()}</RequestTime>
    <OperationTime>{nalog_request_model.operation_time.isoformat()}</OperationTime>
    <IncomeType>FROM_INDIVIDUAL</IncomeType>
    <Services>
        <Amount>{nalog_request_model.amount}</Amount>
        <Name>{nalog_request_model.name}</Name>
        <Quantity>1</Quantity>
    </Services>
    <TotalAmount>{nalog_request_model.amount}</TotalAmount>
    <OperationUniqueId>{nalog_request_model.uuid}</OperationUniqueId>
    {geo_info_block}
</PostIncomeRequestV2>
'''


@send_message_request
def post_cancel_receipt_request(inn, receipt_id, reason_code):
    return f'''
<PostCancelReceiptRequestV2 xmlns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
    <Inn>{inn}</Inn>
    <ReceiptId>{receipt_id}</ReceiptId>
    <ReasonCode>{reason_code}</ReasonCode>
</PostCancelReceiptRequestV2>
'''


@send_message_request
def get_cancel_income_reasons_list_request():
    return f'''
<GetCancelIncomeReasonsListRequest xmlns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
</GetCancelIncomeReasonsListRequest>
'''


@send_message_request
def get_granted_permissions_request(inn):
    return f'''
<tns:GetGrantedPermissionsRequest xmlns:tns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
    <tns:Inn>{inn}</tns:Inn>
</tns:GetGrantedPermissionsRequest>
'''


@send_message_request
def post_platform_registration_request(name, inn, description, partner_text, link, phone, image):
    return f'''
<PostPlatformRegistrationRequest
                xmlns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
    <PartnerName>{name}</PartnerName>
    <PartnerType>PARTNER</PartnerType>
    <PartnerConnectable>true</PartnerConnectable>
    <PartnerAvailableForBind>true</PartnerAvailableForBind>
    <Inn>{inn}</Inn>
    <PartnerDescription>{description}
    </PartnerDescription>
    <PartnersText>{partner_text}</PartnersText>
    <TransitionLink>{link}</TransitionLink>
    <Phone>{phone}</Phone>
    <PartnerImage>{image}</PartnerImage>
</PostPlatformRegistrationRequest>
'''


@send_message_request
def get_newly_unbound_taxpayers_request(from_date, to_date, offset):
    return f'''
<tns:GetNewlyUnboundTaxpayersRequest xmlns:tns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
    <tns:From>{from_date}</tns:From>
    <tns:To>{to_date}</tns:To>
    <tns:Limit>100</tns:Limit>
    <tns:Offset>{offset}</tns:Offset>
</tns:GetNewlyUnboundTaxpayersRequest>
'''


@send_message_request
def get_income_request(inn, from_date, to_date):
    return f'''
<GetIncomeRequestV2 xmlns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
    <Inn>{inn}</Inn>
    <From>{from_date}</From>
    <To>{to_date}</To>
</GetIncomeRequestV2>
'''


@send_message_request
def get_payment_documents_request(inn_list: list):
    inn_list_block = ''

    for inn in inn_list:
        inn_list_block += f'<InnList>{inn}</InnList>'

    return f'''
<GetPaymentDocumentsRequest xmlns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
    {inn_list_block}
</GetPaymentDocumentsRequest>
'''


@send_message_request
def get_keys_request(inn_list: list):
    inn_list_block = ''

    for inn in inn_list:
        inn_list_block += f'<InnList>{inn}</InnList>'

    return f'''
<GetKeysRequest xmlns="urn://x-artefacts-gnivc-ru/ais3/SMZ/SmzPartnersIntegrationService/types/1.0">
    {inn_list_block}
</GetKeysRequest>
'''
