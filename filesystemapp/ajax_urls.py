from . import ajax_views
from django.urls import path

urlpatterns=[
    path("download-all-zip/", ajax_views.download_all_zip, name='download-all-zip'),
    path("download-zip/<str:name>/", ajax_views.download_zip, name='download-zip'),
    path("shared-download-zip/<str:name>/", ajax_views.shared_download_zip, name='shared-download-zip'),
    path("file-explorer/", ajax_views.file_explorer, name='file-explorer'),

]