from django.http import JsonResponse
from .models import Folder, File
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.generic import CreateView
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta
import os
from django.conf import settings


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered!')
            return redirect('register')

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')  
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
            return redirect('register')

    return render(request, 'authentication/register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email') 
        password = request.POST.get('password') 
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user is not None:
            user = authenticate(request, username=user.username, password=password)  
            if user is not None:
                models = ['Folder', 'File']
                app_label = 'filesystemapp'

                for model in models:
                    content_type=ContentType.objects.get(app_label=app_label, model='model')
                    read_permission = Permission.objects.get(codename= f'can_read_{model}', content_type=content_type)
                    permission_codename = f'{app_label}.can_read_{model}'
                    if not user.has_perm(permission_codename):
                        user.user_permissions.add(read_permission)

                request.session.set_expiry(timedelta(hours=2))  
                login(request, user)
                return redirect('home') 
            else:
                messages.error(request, 'Invalid credentials!')
        else:
            messages.error(request, 'No user found with this email address.')

    return render(request, 'authentication/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')


def delete_folder(request):
    if request.method == "POST":
        path = request.POST.get("path")
        if path:
            try:
                folder = Folder.objects.get(name=path)
                folder.delete()
                parent_folder = folder.parent
                if not Folder.objects.filter(parent=parent_folder).exists() and not File.objects.filter(folder=parent_folder).exists():
                   return redirect("/")

                return redirect("/")


            except Folder.DoesNotExist:
                try:
                    file = File.objects.get(id=path)
                    if file.file:  
                        file.file.delete(save=False)
                    file.delete()
                    parent_folder = file.folder
                    if not Folder.objects.filter(parent=parent_folder).exists() and not File.objects.filter(folder=parent_folder).exists():
                        return redirect("/")

                    return redirect("/")
                except File.DoesNotExist:
                    pass
    return redirect("/")


def rename_item(request):
    if request.method == 'POST':
        item_type = request.POST.get('type')
        path = request.POST.get('path')
        new_name = request.POST.get('new_name')

        if item_type == 'folder':
            # Handle renaming folder
            folder = Folder.objects.filter(name=path).first()
            # Check if the new name is different and update the folder's name
            if new_name and new_name != path:
                folder.name = new_name
                folder.save()
            else:
                return HttpResponse("Invalid folder name", status=400)
        
        elif item_type == 'file':
            file = File.objects.filter(name=path).first()
            # Check if the new name is different and update the file's name
            if new_name and new_name != path:
                file.name = new_name
                file.save()
            else:
                return HttpResponse("Invalid file name", status=400)

        return redirect("/")

    return HttpResponse("Invalid request", status=400)




class FileCreateListView(CreateView):
    model = File
    template_name = 'home/pages.html'
    fields = ['name', 'folder', 'file']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        path = self.request.GET.get("path" ) or "root"  
        print(path, "PP")
        parent_folder = None
        if path:
            parent_folder = Folder.objects.filter(name=path).first()
        files = File.objects.filter(folder=parent_folder)
        subfolders = Folder.objects.filter(parent=parent_folder)
        context['files'] = files
        context['folders'] = subfolders
        context['current_path'] = parent_folder
        print(subfolders, "sub")
        return context

    def post(self, request, *args, **kwargs):
        if "folder_name" in self.request.POST:  
            folder_name = self.request.POST.get("folder_name")
            parent_folder_name = self.request.GET.get("path") or "root"
            parent_folder = Folder.objects.filter(name=parent_folder_name).first()

            new_folder=Folder.objects.create(name=folder_name, parent=parent_folder)
            return HttpResponseRedirect(request.path_info + f'?path={request.GET.get("path", "root")}')


        elif "file" in request.FILES:
            files = request.FILES.getlist('file')  
            parent_folder_name = request.GET.get("path") or "root"
            parent_folder = Folder.objects.filter(name=parent_folder_name).first()

            for uploaded_file in files:
                file_instance = File.objects.create(
                    name=uploaded_file.name,
                    folder=parent_folder,
                    file=uploaded_file  
                )

            return HttpResponseRedirect(request.path_info + f'?path={request.GET.get("path", "root")}')
        