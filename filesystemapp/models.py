from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # username = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.username


class Folder(models.Model):
    name = models.CharField(max_length=255, unique=True)
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
    file = models.FileField(upload_to='files')


    def __str__(self):
        return self.name
    
class OTP(models.Model):
    phone_number = models.CharField(max_length=256)
    otp = models.IntegerField(max_length=10)
    generated_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        expiration_time = self.generated_at + timedelta(minutes=5)  
        return timezone.now() > expiration_time
