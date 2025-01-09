from . import ajax_views
from django.urls import path

urlpatterns=[
    path("download-all-zip/", ajax_views.download_all_zip, name='download-all-zip'),
]