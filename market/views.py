import json
from urllib.parse import quote as urlquote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from core.security import throttled
from core.validators import SAFE_LINE

from .forms import (AppointmentForm, ProfileForm, QuoteAnswerForm, QuoteForm,
                    ServiceForm, SupportForm)
from .models import (CATEGORIES, CITIES, Appointment, ArtisanProfile,
                     ContactClick, Quote, Service)


def _visible():
    """Soudeurs dont l'acces (essai ou abonnement) est actif."""
    now = timezone.now()
    return ArtisanProfile.objects.filter(is_suspended=False).filter(
        Q(trial_ends__gt=now) | Q(paid_until__gt=now)).select_related("user")


def _filter(request):
    qs = _visible().annotate(n_services=Count("services", filter=Q(services__is_published=True)))
    city = request.GET.get("ville", "")
    cat = request.GET.get("categorie", "")
    q = (request.GET.get("q", "") or "")[:60].strip()
    if city in dict(CITIES):
        qs = qs.filter(city=city)
    if cat in dict(CATEGORIES):
        qs = qs.filter(services__category=cat, services__is_published=True).distinct()
    if q and SAFE_LINE.match(q):
        qs = qs.filter(Q(business_name__icontains=q) | Q(services__title__icontains=q) | Q(location__icontains=q)).distinct()
    return qs


def home(request):
    featured = _visible().annotate(n_services=Count("services", filter=Q(services__is_published=True)))[:6]
    return render(request, "market/home.html", {"featured": featured, "cities": CITIES, "categories": CATEGORIES})


def artisan_list(request):
    qs = _filter(request)[:60]
    return render(request, "market/list.html", {"artisans": qs, "cities": CITIES, "categories": CATEGORIES,
                                                 "sel_city": request.GET.get("ville", ""), "sel_cat": request.GET.get("categorie", ""),
                                                 "q": request.GET.get("q", "")[:60]})


@require_GET
@throttled("api-list", limit=120, window=60)
def api_artisans(request):
    data = [{
        "id": a.pk, "name": a.business_name, "city": a.city, "location": a.location,
        "years": a.years_experience, "verified": a.is_verified, "services": a.n_services,
        "url": f"/soudeurs/{a.pk}/",
    } for a in _filter(request)[:60]]
    return JsonResponse({"results": data})


def artisan_detail(request, pk):
    p = get_object_or_404(_visible(), pk=pk)
    data = {
        "@context": "https://schema.org", "@type": "LocalBusiness", "name": p.business_name,
        "address": {"@type": "PostalAddress", "streetAddress": p.location, "addressLocality": p.city, "addressCountry": "CM"},
        "url": request.build_absolute_uri(),
    }
    jsonld = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return render(request, "market/detail.html", {"p": p, "services": p.services.filter(is_published=True), "jsonld": jsonld})


@require_POST
@throttled("api-contact", limit=20, window=300)
def api_contact(request, pk):
    p = get_object_or_404(_visible(), pk=pk)
    ContactClick.objects.create(profile=p)
    text = urlquote(f"Bonjour {p.business_name}, je vous contacte depuis MetalLink pour un travail de soudure.")
    return JsonResponse({"url": f"https://wa.me/{p.whatsapp}?text={text}", "phone": p.phone})


@login_required
def profile_edit(request):
    if request.user.role != "artisan" or not hasattr(request.user, "profile"):
        raise Http404
    form = ProfileForm(request.POST or None, instance=request.user.profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profil mis à jour.")
        return redirect("accounts:dashboard")
    return render(request, "market/form.html", {"form": form, "title": "Mon profil et mon lieu d'exercice"})


def _artisan_or_404(request):
    if request.user.role != "artisan" or not hasattr(request.user, "profile"):
        raise Http404
    return request.user.profile


@login_required
def service_edit(request, pk=None):
    p = _artisan_or_404(request)
    obj = get_object_or_404(Service, pk=pk, profile=p) if pk else None
    if not p.has_access:
        messages.error(request, "Votre accès est expiré. Renouvelez votre abonnement pour publier ou modifier vos services.")
        return redirect("billing:pay")
    form = ServiceForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        s = form.save(commit=False)
        s.profile = p
        s.save()
        messages.success(request, "Service enregistré.")
        return redirect("accounts:dashboard")
    return render(request, "market/form.html", {"form": form, "title": "Modifier le service" if obj else "Nouveau service"})


@login_required
@require_POST
def service_delete(request, pk):
    p = _artisan_or_404(request)
    get_object_or_404(Service, pk=pk, profile=p).delete()
    messages.success(request, "Service supprimé.")
    return redirect("accounts:dashboard")


@login_required
@throttled("rdv", limit=15, window=3600)
def appointment_create(request, pk):
    p = get_object_or_404(_visible(), pk=pk)
    if request.user.role != "client":
        messages.error(request, "Seuls les clients peuvent prendre rendez-vous.")
        return redirect("market:detail", pk=pk)
    form = AppointmentForm(request.POST or None, profile=p)
    if request.method == "POST" and form.is_valid():
        a = form.save(commit=False)
        a.client, a.profile = request.user, p
        a.save()
        messages.success(request, "Demande de rendez-vous envoyée au soudeur.")
        return redirect("accounts:dashboard")
    return render(request, "market/form.html", {"form": form, "title": f"Rendez-vous avec {p.business_name}"})


@login_required
@require_POST
def appointment_status(request, pk, status):
    a = get_object_or_404(Appointment, pk=pk)
    if status not in ("confirmed", "declined", "done", "cancelled"):
        raise Http404
    owner_artisan = hasattr(request.user, "profile") and a.profile_id == request.user.profile.pk
    if status == "cancelled" and a.client_id == request.user.pk:
        pass
    elif not owner_artisan or status == "cancelled":
        raise Http404
    a.status = status
    a.save(update_fields=["status"])
    return redirect("accounts:dashboard")


@login_required
@throttled("devis", limit=15, window=3600)
def quote_create(request, pk):
    p = get_object_or_404(_visible(), pk=pk)
    if request.user.role != "client":
        messages.error(request, "Seuls les clients peuvent demander un devis.")
        return redirect("market:detail", pk=pk)
    form = QuoteForm(request.POST or None, initial={"city": p.city})
    if request.method == "POST" and form.is_valid():
        q = form.save(commit=False)
        q.client, q.profile = request.user, p
        q.save()
        messages.success(request, "Demande de devis envoyée.")
        return redirect("accounts:dashboard")
    return render(request, "market/form.html", {"form": form, "title": f"Demande de devis : {p.business_name}"})


@login_required
def quote_answer(request, pk):
    p = _artisan_or_404(request)
    q = get_object_or_404(Quote, pk=pk, profile=p)
    form = QuoteAnswerForm(request.POST or None, instance=q)
    if request.method == "POST" and form.is_valid():
        q = form.save(commit=False)
        q.status = "answered"
        q.save()
        messages.success(request, "Devis envoyé au client.")
        return redirect("accounts:dashboard")
    return render(request, "market/form.html", {"form": form, "title": "Répondre à la demande de devis", "quote": q})


@login_required
@require_POST
def quote_decide(request, pk, decision):
    q = get_object_or_404(Quote, pk=pk, client=request.user, status="answered")
    if decision not in ("accepted", "refused"):
        raise Http404
    q.status = decision
    q.save(update_fields=["status"])
    return redirect("accounts:dashboard")


@throttled("support", limit=6, window=3600)
def support(request):
    initial = {}
    if request.user.is_authenticated:
        initial = {"name": request.user.full_name, "email": request.user.email}
    form = SupportForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        m = form.save(commit=False)
        m.user = request.user if request.user.is_authenticated else None
        m.save()
        messages.success(request, "Message envoyé. Nous vous répondons rapidement.")
        return redirect("market:support")
    return render(request, "market/support.html", {"form": form})


def legal(request, page):
    if page not in ("cgu", "confidentialite"):
        raise Http404
    return render(request, f"market/{page}.html")
