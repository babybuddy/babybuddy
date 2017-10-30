from django.conf import settings

def date_formats(request):
    return {'MOMENTJS_FORMAT': settings.MOMENTJS_FORMAT}
