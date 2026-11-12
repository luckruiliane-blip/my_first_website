from django.contrib.sitemaps import Sitemap
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_GET

from market.views import _visible


class PagesSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ["market:home", "market:list", "market:support", "accounts:register"]

    def location(self, item):
        return reverse(item)


class ArtisansSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return _visible().order_by("pk")

    def location(self, obj):
        return reverse("market:detail", args=[obj.pk])


@require_GET
def robots(request):
    lines = [
        "User-agent: *",
        "Disallow: /api/",
        "Disallow: /espace/",
        "Disallow: /connexion/",
        "Disallow: /abonnement/",
        "Disallow: /mes-services/",
        "Disallow: /mon-profil/",
        "Disallow: /rendez-vous/",
        "Disallow: /devis/",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
