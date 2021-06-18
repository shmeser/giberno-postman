from django.urls import path

from app_users.views import AuthFirebase, AuthRefreshToken, firebase_web_auth, ReferenceCode, AuthVk, Users, \
    MyProfile, MyProfileUploads, MyProfileSocials, Notifications, NotificationsSettings, MyProfileCareer, \
    MyProfileDocuments, read_notification, CreateManagerByAdminAPIView, GetManagerByUsernameAPIView, \
    AuthenticateManagerAPIView, ChangeManagerPasswordAPIView, EditManagerProfileView, PushUnsubscribe, push_subscribe, \
    CreateSecurityByAdmin, AuthenticateSecurity, UsersRating

urlpatterns = [
    path('auth/firebase/web', firebase_web_auth),
    path('auth/firebase', AuthFirebase.as_view()),
    path('auth/refresh', AuthRefreshToken.as_view()),
    path('auth/reference', ReferenceCode.as_view()),
    path('auth/vk', AuthVk.as_view()),

    # SECURITY AUTH
    path('auth/security/login', AuthenticateSecurity.as_view()),
    # ###

    path('users', Users.as_view()),
    path('users/<int:record_id>', Users.as_view()),

    path('users/profile', MyProfile.as_view()),
    path('users/profile/upload', MyProfileUploads.as_view()),
    path('users/profile/career', MyProfileCareer.as_view()),
    path('users/profile/career/<int:record_id>', MyProfileCareer.as_view()),

    path('users/profile/socials', MyProfileSocials.as_view()),

    path('users/profile/documents', MyProfileDocuments.as_view()),
    path('users/profile/documents/<int:record_id>', MyProfileDocuments.as_view()),

    path('users/rating', UsersRating.as_view()),

    path('notifications', Notifications.as_view()),
    path('notifications/<int:record_id>', Notifications.as_view()),
    path('notifications/<int:record_id>/read', read_notification),
    path('notifications/settings', NotificationsSettings.as_view()),
    path('notifications/subscribe', push_subscribe),
    path('notifications/unsubscribe', PushUnsubscribe.as_view()),

    # MANAGERS RELATED URLS
    path('admin/managers', CreateManagerByAdminAPIView.as_view()),
    path('users/managers/username', GetManagerByUsernameAPIView.as_view()),
    path('users/managers/login', AuthenticateManagerAPIView.as_view()),
    path('users/managers/password/change', ChangeManagerPasswordAPIView.as_view()),
    path('users/managers/profile', EditManagerProfileView.as_view()),

    # CREATE SECURITY
    path('admin/security', CreateSecurityByAdmin.as_view()),
]
