from django.urls import path

from app_users.views import Users, AuthFirebase, AuthRefreshToken, firebase_web_auth, ReferenceCode

urlpatterns = [
    path('auth/firebase/web', firebase_web_auth),
    path('auth/firebase', AuthFirebase.as_view()),
    path('auth/refresh', AuthRefreshToken.as_view()),
    path('auth/reference', ReferenceCode.as_view()),

    path('users', Users.as_view()),
]
