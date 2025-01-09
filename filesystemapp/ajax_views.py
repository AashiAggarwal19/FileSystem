
import tarfile
from .models import Folder, File
from django.contrib.auth.models import User
import os
import shutil
from django.core.files.storage import default_storage
from django.conf import settings
from django.http import HttpResponse

def get_all_related_folders(folder=None, zip_file="file", base_path="file"):
    """
    Recursively fetches all subfolders of the given folder and includes files in the specified folder.
    If folder is None, it processes root-level files.
    """
    if folder:
        subfolders = folder.subfolders.all()  
        files = folder.files.all()  
        folder_path_in_zip = os.path.join(base_path, folder.name)
        os.makedirs(folder_path_in_zip, exist_ok=True)  

        for file in files:
            file_path = file.file.name
            source_path = os.path.join(settings.MEDIA_ROOT, file_path)

            if not default_storage.exists(source_path):  
                os.remove(source_path)  
                continue
            destination_path = os.path.join(folder_path_in_zip, os.path.basename(file_path))
            shutil.copy(source_path, destination_path)

        for subfolder in subfolders:
            get_all_related_folders(subfolder, zip_file, folder_path_in_zip)
    else:
        root_files = File.objects.filter(folder__isnull=True)  
        for file in root_files:
            file_path = file.file.name
            source_path = os.path.join(settings.MEDIA_ROOT, file_path)
            if not default_storage.exists(source_path):  
                os.remove(source_path)  
                continue

            destination_path = os.path.join(base_path, os.path.basename(file_path))
            shutil.copy(source_path, destination_path)


def download_all_zip(request):
    documents = Folder.objects.filter(parent__isnull=True)  

    if not documents and not File.objects.filter(folder__isnull=True):
        return HttpResponse("No folders or files found.", status=404)

    folder_path = "file"
    os.makedirs(folder_path, exist_ok=True)
    get_all_related_folders(folder=None, base_path=folder_path)

    for document in documents:
        get_all_related_folders(document, base_path=folder_path)
    
    tar_folder = "zipped_folder"
    os.makedirs(tar_folder, exist_ok=True)
    tar_file_path = os.path.join(tar_folder, "folder.tar")
    with tarfile.open(tar_file_path, "w") as tar:
        tar.add(folder_path, arcname=os.path.basename(folder_path))

    shutil.rmtree(folder_path)

    with open(tar_file_path, "rb") as tar_file:
        response = HttpResponse(tar_file.read(), content_type="application/x-tar")
        response["Content-Disposition"] = 'attachment; filename="folder.tar"'

    return response