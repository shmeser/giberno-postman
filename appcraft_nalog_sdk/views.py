import datetime
import json

from django.http import JsonResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from appcraft_nalog_sdk import tasks
from appcraft_nalog_sdk.models import NalogNotificationModel, NalogUser, NalogIncomeRequestModel
from appcraft_nalog_sdk.sdk import NalogSdk
from appcraft_nalog_sdk.serializers import NalogNotificationSerializer, NalogUserSerializer


class UpdateStatuses(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        tasks.update_processing_statuses()
        return JsonResponse({})


class StatusView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        inn = request.GET.get('inn')

        nalog_sdk = NalogSdk()
        nalog_sdk.get_status(inn=inn)
        nalog_sdk.update_processing_statuses()

        user = NalogUser.get_or_create(inn)

        return Response(NalogUserSerializer(user).data)


class NotificationsView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = NalogNotificationSerializer

    def get_queryset(self):
        inn = self.request.GET.get('inn')
        nalog_sdk = NalogSdk()
        nalog_sdk.get_notifications(inn=inn)
        nalog_sdk.update_processing_statuses()

        return NalogNotificationModel.get_unread_notifications(inn)

    def patch(self, request):
        nalog_sdk = NalogSdk()

        notifications = NalogNotificationModel.objects.filter(user__inn=request.GET.get('inn')).exclude(
            status='ACKNOWLEDGED')
        notification_ids = [notification[0] for notification in notifications.values_list('notification_id')]

        nalog_sdk.read_notifications(request.GET.get('inn'), notification_ids)
        return JsonResponse({})


class BindView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        inn = request.GET.get('inn')
        nalog_sdk = NalogSdk()
        nalog_sdk.get_bind_partner_status_request(inn=inn)
        nalog_sdk.update_processing_statuses()
        user = NalogUser.get_or_create(inn)

        return Response(NalogUserSerializer(user).data)

    def post(self, request):
        inn = request.data['inn']
        nalog_sdk = NalogSdk()
        nalog_sdk.post_bind_partner_with_inn_request(inn=inn)
        nalog_sdk.update_processing_statuses()
        user = NalogUser.get_or_create(inn)

        return Response(NalogUserSerializer(user).data)


class PostIncomeView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        tasks.get_income_request()
        return JsonResponse({})

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))

        inn = data['inn']
        request_time = datetime.datetime.fromisoformat(data['request_time'])
        operation_time = datetime.datetime.fromisoformat(data['operation_time'])
        amount = data['amount']
        name = data['name']
        latitude = data.get('latitude', None)
        longitude = data.get('longitude', None)

        nalog_sdk = NalogSdk()
        nalog_income_request = NalogIncomeRequestModel.create(inn, amount, name, operation_time,
                                                              request_time, latitude,
                                                              longitude)

        nalog_sdk.post_income_request(nalog_income_request)
        return JsonResponse({})

    def delete(self, request):
        data = json.loads(request.body.decode('utf-8'))

        receipt_id = data['receiptId']
        reason_code = data['reasonCode']

        nalog_sdk = NalogSdk()
        nalog_sdk.post_cancel_receipt_request(receipt_id, reason_code)

        return JsonResponse({})


class CancelReasons(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        nalog_sdk = NalogSdk()
        nalog_sdk.get_cancel_income_reasons_list_request()

        return JsonResponse({})


class GrantedPermissionsView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        tasks.get_granted_permissions_request()

        return JsonResponse({})


class PlatformRegistrationView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))

        name = data['name']
        inn = data['inn']
        description = data['description']
        partner_text = data['partner_text']
        link = data['link']
        phone = data['phone']
        image = data['image']

        nalog_sdk = NalogSdk()
        nalog_sdk.post_platform_registration_request(name, inn, description, partner_text, link, phone, image)

        return JsonResponse({})


class GetNewlyUnboundTaxpayersRequest(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        tasks.get_newly_unbound_taxpayers_request()
        return JsonResponse({})


class GetPaymentDocumentsRequest(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        tasks.get_payment_documents_request()
        return JsonResponse({})
