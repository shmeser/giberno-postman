from django.urls import path

from app_admin import views

urlpatterns = [
    path('admin/access_rights/staff', views.Staff.as_view()),
    path('admin/access_rights/content_types', views.AccessContentTypes.as_view()),
    path('admin/access_rights', views.UsersAccess.as_view()),
    path('admin/access_rights/<int:record_id>', views.UserAccess.as_view()),
]

