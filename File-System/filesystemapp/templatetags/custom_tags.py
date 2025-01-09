from django import template

register = template.Library()

@register.filter
def file_type(file_name):
    ext = file_name.lower().split('.')[-1]
    if ext in ['jpg', 'jpeg', 'png']:
        return 'image'
    elif ext in ['txt']:
        return 'text'
    elif ext in ['html']:
        return 'code'
    elif ext in ['xls', 'xlsx', 'csv']:
        return 'excel'
    elif ext in ['pdf']:
        return 'pdf'
    elif ext in ['doc', 'docx']:
        return 'word'
    else:
        return 'file'
