from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from django.contrib.sitemaps.views import sitemap

from core import seo
from core import views as core_views
from core.security import is_owner

# Seul le proprietaire configure peut passer ; tout autre visiteur recoit une 404.
admin.site.has_permission = lambda request: is_owner(request.user, request)
admin.site.site_header = "MetalLink : administration"
admin.site.site_title = "MetalLink"

SITEMAPS = {"pages": seo.PagesSitemap, "soudeurs": seo.ArtisansSitemap}

urlpatterns = [
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt", seo.robots, name="robots"),
    path(f"{settings.ADMIN_PATH}/tableau/", core_views.pilotage, name="pilotage"),
    path(f"{settings.ADMIN_PATH}/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("billing.urls")),
    path("", include("market.urls")),
]
