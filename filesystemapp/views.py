from django.http import JsonResponse
from .models import Folder, File, CustomUser, OTP
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
from .models import CustomUser  
import requests
from django.utils import timezone
from random import randint

def send_otp(phone_number):
    print("isnisde this")
    otp = randint(100000, 999999)  
    url = 'https://www.fast2sms.com/dev/bulkV2'
    headers = {
        'authorization': '67tlumBYVdfC0xQEsSRoOezDMbWHXcL2njwkay5NAi4gJrqFpTjAYpsx6mPZtNk7hRV4IbUXWe8C1JcG',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    msg = "177601"
    data = f'sender_id=MOAPPP&message={msg}&variables_values={otp}&route=dlt&numbers={phone_number}'
    
    response = requests.post(url, headers=headers, data=data)
    print(response.json(), "kjbkjbghjn")
    if response.status_code == 200:
        OTP.objects.update_or_create(
            phone_number=phone_number,
            defaults={'otp': otp, 'generated_at': timezone.now()},
        )
        return True
    else:
        return False


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        phone_number = request.POST.get('phone_number')
        
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('register')

        if CustomUser.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'Phone Number is already registered!')
            return redirect('register')

        try:
            user = CustomUser.objects.create(username=username, phone_number=phone_number)
            user.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')  
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
            return redirect('register')

    return render(request, 'authentication/register.html')

def login_view(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        otp = request.POST.get('otp') 
        action = request.POST.get("action")

        if action == 'send_otp' or action == 'resend_otp':
            try:
                user = CustomUser.objects.get(phone_number=phone_number)
                if send_otp(phone_number):  
                    messages.success(request, 'OTP has been sent to your phone number.')
                    return render(request, 'authentication/login.html', {'show_otp': True, 'phone_number': phone_number})
                else:
                    messages.error(request, 'Failed to send OTP. Please try again.')
            except CustomUser.DoesNotExist:
                messages.error(request, "User with this phone number does not exist.")
            return render(request, 'authentication/login.html')
    
        elif action == 'verify_otp': 
            try:
                otp_record = OTP.objects.get(phone_number=phone_number, otp=otp)
                if otp_record.is_expired():
                    messages.error(request, "OTP has expired.")
                else:
                    user = CustomUser.objects.get(phone_number=phone_number)
                    login(request, user)
                    return redirect('/')  
            except OTP.DoesNotExist:
                    messages.error(request, "Invalid OTP.")
            return render(request, 'authentication/login.html', {'show_otp': True, 'phone_number': phone_number})

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
        