from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from app_users.models import UserProfile


class GetUserTokenTestAPIView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        user = UserProfile.objects.get(id=self.kwargs['pk'])
        return Response(str(RefreshToken.for_user(user=user).access_token))
