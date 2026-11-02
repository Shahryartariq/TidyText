from django.conf import settings


def site(request):
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "site_url": request.site_url,
        "canonical_url": request.site_url + request.path,
        "ga_id": settings.GA_MEASUREMENT_ID,
        "analytics_enabled": bool(settings.GA_MEASUREMENT_ID),
    }
