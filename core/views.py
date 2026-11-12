from datetime import timedelta

from django.conf import settings
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.http import Http404
from django.shortcuts import render
from django.utils import timezone

from accounts.models import User
from billing.models import Payment
from market.models import Appointment, ArtisanProfile, ContactClick, Quote, SupportMessage

from .security import is_owner


def pilotage(request):
    if not is_owner(request.user, request):
        raise Http404
    now = timezone.now()
    since = now - timedelta(days=30)
    signups = (User.objects.filter(date_joined__gte=since).annotate(d=TruncDate("date_joined"))
               .values("d").annotate(n=Count("id")).order_by("d"))
    peak = max([s["n"] for s in signups] or [1])
    ctx = {
        "kpi": [
            ("Clients", User.objects.filter(role="client").count()),
            ("Soudeurs", ArtisanProfile.objects.count()),
            ("Soudeurs en essai", ArtisanProfile.objects.filter(paid_until__isnull=True, trial_ends__gt=now).count()),
            ("Abonnés actifs", ArtisanProfile.objects.filter(paid_until__gt=now).count()),
            ("Accès expirés", sum(1 for p in ArtisanProfile.objects.all() if p.access_until <= now)),
            ("Rendez-vous", Appointment.objects.count()),
            ("Demandes de devis", Quote.objects.count()),
            ("Clics contact", ContactClick.objects.count()),
            ("Messages non traités", SupportMessage.objects.filter(handled=False).count()),
        ],
        "revenue": Payment.objects.filter(status="success").aggregate(t=Sum("amount"))["t"] or 0,
        "signups": [{"d": s["d"], "n": s["n"], "w": int(s["n"] * 100 / peak)} for s in signups],
        "users": User.objects.order_by("-date_joined")[:15],
        "artisans": ArtisanProfile.objects.select_related("user").order_by("-created_at")[:15],
        "payments": Payment.objects.select_related("user")[:15],
        "support_msgs": SupportMessage.objects.all()[:15],
        "appointments": Appointment.objects.select_related("client", "profile")[:15],
        "admin_path": settings.ADMIN_PATH,
    }
    return render(request, "pilotage/dashboard.html", ctx)
