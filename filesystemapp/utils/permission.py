from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


def create_permissions():
    models = ['Folder', 'File'] 
    for model in models:
        content_type = ContentType.objects.get(app_label='filesystemapp', model=model)

        permissions = [
            ('can_read', f'Can read {model}s'),
            ('can_write', f'Can write {model}s'),
            ('can_download', f'Can download {model}s'),
            ('can_delete', f'Can delete {model}s'),
        ]

        for codename, name in permissions:
            Permission.objects.get_or_create(codename=f"{codename}_{model}", name=name, content_type=content_type)
