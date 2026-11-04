from django.templatetags.static import static
from django.urls import path
from django.views.generic.base import RedirectView

from tools import views

urlpatterns = [
    path("", views.tool_page, name="home"),
    path("about/", views.about, name="about"),
    path("privacy/", views.privacy, name="privacy"),
    path("robots.txt", views.robots_txt, name="robots"),
    path(
        views.GOOGLE_VERIFICATION_FILE,
        views.google_site_verification,
        name="google_site_verification",
    ),
    path("healthz", views.healthz, name="healthz"),
    path(
        "favicon.ico",
        RedirectView.as_view(url=static("img/favicon.ico"), permanent=True),
        name="favicon",
    ),
    path("<slug:slug>/", views.tool_page, name="tool"),
]
