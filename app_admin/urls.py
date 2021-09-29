from django.urls import path

from app_admin import views

urlpatterns = [
    path('admin/api-keys', views.ApiKeys.as_view()),
    path('admin/api-keys/<int:record_id>', views.ApiKey.as_view()),
    path('admin/access/staff', views.Staff.as_view()),
    path('admin/access/staff/<int:record_id>', views.StaffMember.as_view()),
    path('admin/access/content_types', views.AccessContentTypes.as_view()),
    path('admin/access', views.UsersAccess.as_view()),
    path('admin/access/<int:record_id>', views.UserAccess.as_view()),
]

