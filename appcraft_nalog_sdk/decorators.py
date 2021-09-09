def auth_message_request(function_to_decorate):
    def wrapper(*args):
        body = function_to_decorate(*args)
        return f'''
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="urn://x-artefacts-gnivc-ru/inplat/servin/OpenApiMessageConsumerService/types/1.0">
    <soapenv:Header/>
    <soapenv:Body>
        <ns:GetMessageRequest>
            <ns:Message>
                {body}
            </ns:Message>
        </ns:GetMessageRequest>
    </soapenv:Body>
</soapenv:Envelope>

        '''

    return wrapper


def get_message_by_id(function_to_decorate):
    def wrapper(*args):
        body = function_to_decorate(*args)
        return f'''
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <GetMessageRequest xmlns="urn://x-artefacts-gnivc-ru/inplat/servin/OpenApiAsyncMessageConsumerService/types/1.0">
            {body}
        </GetMessageRequest>
    </soap:Body>
</soap:Envelope>
        '''

    return wrapper


def send_message_request(function_to_decorate):
    def wrapper(*args):
        body = function_to_decorate(*args)
        return f'''
<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">
    <soap-env:Body>
        <ns0:SendMessageRequest
                xmlns:ns0="urn://x-artefacts-gnivc-ru/inplat/servin/OpenApiAsyncMessageConsumerService/types/1.0">
            <ns0:Message>
                {body}
            </ns0:Message>
        </ns0:SendMessageRequest>
    </soap-env:Body>
</soap-env:Envelope>
        '''

    return wrapper
