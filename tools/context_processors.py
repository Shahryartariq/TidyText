from django.conf import settings


def site(request):
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "site_url": request.site_url,
        "canonical_url": request.site_url + request.path,
    }
