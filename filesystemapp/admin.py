from django.contrib import admin
from .models import Folder, File  # Import the models

# Register the Folder model
admin.site.register(Folder)

# Register the File model
admin.site.register(File)