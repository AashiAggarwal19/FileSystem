from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Phone number is required")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, password, **extra_fields)

class CustomUser(AbstractBaseUser,PermissionsMixin):
    phone_number = models.CharField(max_length=15, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    permissions = models.IntegerField(default=1)  


    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number



class Folder(models.Model):
    name = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(CustomUser,on_delete=models.RESTRICT, related_name='owned_folders')
    shared_by = models.ManyToManyField(CustomUser, related_name='shared_folders')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    path = models.CharField(max_length=1024, null=True)


    def save(self, *args, **kwargs):
        if self.parent:
            self.path = f"{self.parent.path}/{self.name}"
        else:
            self.path = self.name
        super().save(*args, **kwargs)

    def __str__(self):        
        return self.path if self.path else f"Folder: {self.name}"

class File(models.Model):
    name = models.CharField(max_length=255, unique=True)
    folder = models.ForeignKey(Folder, null=True, blank=True, on_delete=models.CASCADE, related_name='files')
    user = models.ForeignKey(CustomUser,on_delete=models.RESTRICT, related_name='owned_files')
    shared_by = models.ManyToManyField(CustomUser, related_name='shared_files')
    file = models.FileField(upload_to='files')


    def __str__(self):
        return self.name

    
class OTP(models.Model):
    phone_number = models.CharField(max_length=256)
    otp = models.IntegerField()
    generated_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        expiration_time = self.generated_at + timedelta(minutes=5)  
        return timezone.now() > expiration_time
    
class SharedFilePath(models.Model):
    file = models.OneToOneField(File, on_delete=models.CASCADE, related_name='shared_path')
    path = models.CharField(max_length=1024)  
    shared_by = models.ManyToManyField(CustomUser, related_name='shared_file_paths')

    def __str__(self):
        return f"{self.file.name} ({self.path})"
