
import tarfile
from .models import Folder, File, CustomUser
import os
import shutil
from django.core.files.storage import default_storage
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from datetime import datetime
import random

def get_all_related_folders(folder=None, zip_file="file", base_path="file", user=None):
    """
    Recursively fetches all subfolders of the given folder and includes files in the specified folder.
    If folder is None, it processes root-level files.
    """
    if folder:
        # subfolders = folder.subfolders.all()  
        # files = folder.files.all()  
        subfolders = folder.subfolders.filter(user=user) 
        files = folder.files.filter(user=user) 
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
            get_all_related_folders(subfolder, zip_file, folder_path_in_zip, user)
    else:
        root_files = File.objects.filter(folder__isnull=True, user=user)  if user else File.objects.filter(folder__isnull=True)
        
        for file in root_files:
            file_path = file.file.name

            source_path = os.path.join(settings.MEDIA_ROOT, file_path)
            if not default_storage.exists(source_path):  
                os.remove(source_path)  
                continue

            destination_path = os.path.join(base_path, os.path.basename(file_path))
            shutil.copy(source_path, destination_path)

def download_all_zip(request):
    documents = Folder.objects.filter(parent__isnull=True, user=request.user)  

    if not documents and not File.objects.filter(folder__isnull=True, user = request.user):
        return HttpResponse("No folders or files found.", status=404)
    random_dig = random.randint(00000,1002039300)
    folder_path = "file"
    os.makedirs(folder_path, exist_ok=True)
    get_all_related_folders(folder=None, base_path=folder_path, user = request.user)

    for document in documents:
        get_all_related_folders(document, base_path=folder_path, user=request.user)
    
    tar_folder = "zipped_folder"
    os.makedirs(tar_folder, exist_ok=True)
    tar_file_path = os.path.join(tar_folder, f"folder{random_dig}.tar")
    with tarfile.open(tar_file_path, "w") as tar:
        tar.add(folder_path, arcname=os.path.basename(folder_path))

    shutil.rmtree(folder_path)

    with open(tar_file_path, "rb") as tar_file:
        response = HttpResponse(tar_file.read(), content_type="application/x-tar")
        response["Content-Disposition"] = f'attachment; filename="folder{random_dig}.tar"'

    return response

def download_zip(request, name):
    try:
         folder= Folder.objects.get(name=name, user=request.user)
    except Folder.DoesNotExist: 
         return HttpResponse("Folder Not Found!", status=404)
    
    folder = Folder.objects.get(name=name)

    folder_path = "file"
    os.makedirs(folder_path, exist_ok=True)
    get_all_related_folders(folder=folder, base_path=folder_path, user=request.user)

    tar_folder = "zipped_folder"
    os.makedirs(tar_folder, exist_ok=True)
    tar_file_path = os.path.join(tar_folder, f"{name}.tar")
    with tarfile.open(tar_file_path, "w") as tar:
        tar.add(folder_path, arcname=os.path.basename(folder_path))

    shutil.rmtree(folder_path)

    with open(tar_file_path, "rb") as tar_file:
        response = HttpResponse(tar_file.read(), content_type="application/x-tar")
        response["Content-Disposition"] = f'attachment; filename="{name}.tar"'

    return response

def shared_download_zip(request, name):
    try:
        folder = Folder.objects.get(name=name)
    except Folder.DoesNotExist:
        return HttpResponse("Folder Not Found!", status=404)

    if request.user not in folder.shared_by.all():
        return HttpResponse("You don't have permission to access this folder.", status=403)

    folder_path = "file"
    os.makedirs(folder_path, exist_ok=True)

    def add_folder_files_to_zip(folder, base_path):
        subfolders = folder.subfolders.all()
        files = folder.files.all()

        folder_path_in_zip = os.path.join(base_path, folder.name)
        os.makedirs(folder_path_in_zip, exist_ok=True)

        for file in files:
            file_path = file.file.name
            source_path = os.path.join(settings.MEDIA_ROOT, file_path)

            if os.path.exists(source_path):  
                destination_path = os.path.join(folder_path_in_zip, os.path.basename(file_path))
                shutil.copy(source_path, destination_path)

        for subfolder in subfolders:
            add_folder_files_to_zip(subfolder, folder_path_in_zip)

    add_folder_files_to_zip(folder, folder_path)

    tar_folder = "zipped_folder"
    os.makedirs(tar_folder, exist_ok=True)
    tar_file_path = os.path.join(tar_folder, f"{name}_shared_folder.tar")

    with tarfile.open(tar_file_path, "w") as tar:
        tar.add(folder_path, arcname=os.path.basename(folder_path))

    shutil.rmtree(folder_path)

    with open(tar_file_path, "rb") as tar_file:
        response = HttpResponse(tar_file.read(), content_type="application/x-tar")
        response["Content-Disposition"] = f'attachment; filename="{name}_shared_folder.tar"'

    return response


def file_explorer(request):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            path = request.GET.get("path") or "root"
            parent_folder = None
            if path != "root":
                folder_names = path.split("/")  
                parent_folder = None
                for folder_name in folder_names:
                    parent_folder = Folder.objects.filter(name=folder_name, parent=parent_folder, user=request.user).first()

            files = File.objects.filter(folder=parent_folder, user=request.user) 
            subfolders = Folder.objects.filter(parent=parent_folder, user=request.user) 

            return JsonResponse({
                "files": list(files.values('name')),
                "folders": list(subfolders.values('name')),
                "current_path": path
            })

        return JsonResponse({"error": "Invalid request"}, status=400)

    
