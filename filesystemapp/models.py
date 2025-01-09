from django.db import models

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
