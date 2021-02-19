from rest_framework.views import APIView


class BaseAPIView(APIView):
    serializer_class = None

    def get_serializer(self):
        return self.serializer_class()
