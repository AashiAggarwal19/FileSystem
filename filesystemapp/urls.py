from . import views
from django.urls import path

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # path('home/', views.home, name='home'),
    # path("upload-file/", views.upload_file, name="upload_file"),
    path('delete-folder/', views.delete_folder, name='delete-folder'),    
    path("rename-item/", views.rename_item, name="rename-item"),
    path("", views.FileCreateListView.as_view(), name="get-file-system"),
]