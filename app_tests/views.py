from djangorestframework_camel_case.util import camelize
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from app_sockets.controllers import SocketController
from app_users.models import UserProfile
from backend.controllers import PushController
from backend.utils import get_request_body, chained_get


class GetUserTokenTestAPIView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        user = UserProfile.objects.get(id=self.kwargs['pk'])
        return Response(str(RefreshToken.for_user(user=user).access_token))


class SendTestPush(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        body = get_request_body(request)
        PushController().send_notification(
            users_to_send=[request.user],
            title=chained_get(body, 'title') or '',
            message=chained_get(body, 'message') or '',
            action=chained_get(body, 'action'),
            subject_id=chained_get(body, 'subject_id'),
            notification_type=chained_get(body, 'notification_type'),
            icon_type=chained_get(body, 'icon_type'),
        )

        # Отправка уведомления по сокетам
        SocketController(request.user).send_single_notification({
            'title': chained_get(body, 'title') or '',
            'message': chained_get(body, 'message') or '',
            'action': chained_get(body, 'action'),
            'subjectId': chained_get(body, 'subject_id'),
            'notificationType': chained_get(body, 'notification_type'),
            'iconType': chained_get(body, 'icon_type'),
        })
        return Response(camelize(body), status=status.HTTP_200_OK)
