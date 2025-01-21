from django.contrib import admin
from .models import Folder, File,CustomUser  # Import the models


admin.site.register(CustomUser)
admin.site.register(Folder)

admin.site.register(File)
