from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.decorators.cache import cache_control

from tools.sitemaps import SITEMAPS

urlpatterns = [
    path(
        "sitemap.xml",
        cache_control(public=True, max_age=3600)(sitemap),
        {"sitemaps": SITEMAPS},
        name="sitemap",
    ),
    path("", include("tools.urls")),
]

handler404 = "tools.views.page_not_found"
handler500 = "tools.views.server_error"
