import hmac
import uuid

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from core.forms import PhoneField, StyledMixin
from core.notify import notify_admin
from core.security import throttled

from . import providers
from .models import Payment


class PayForm(StyledMixin, forms.Form):
    operator = forms.ChoiceField(label="Opérateur", choices=Payment.OPERATORS, widget=forms.RadioSelect)
    phone = PhoneField(label="Numéro qui paie")


def _apply(payment):
    """Marque le paiement comme reussi une seule fois et prolonge l'acces."""
    if payment.status == "success":
        return
    payment.status = "success"
    payment.paid_at = timezone.now()
    payment.save(update_fields=["status", "paid_at"])
    payment.user.profile.extend(settings.SUBSCRIPTION_DAYS)
    notify_admin("Paiement reçu", [f"{payment.user.email}", f"{payment.amount} FCFA", payment.operator])


def _refresh(payment):
    if payment.status != "pending" or not payment.provider_ref:
        return
    try:
        s = providers.status(payment.provider_ref)
    except providers.ProviderError:
        return
    if s == "success":
        _apply(payment)
    elif s == "failed":
        payment.status = "failed"
        payment.save(update_fields=["status"])


@login_required
@throttled("pay", limit=6, window=3600)
@require_http_methods(["GET", "POST"])
def pay(request):
    if request.user.role != "artisan" or not hasattr(request.user, "profile"):
        raise Http404
    p = request.user.profile
    form = PayForm(request.POST or None, initial={"phone": request.user.phone[3:]})
    if request.method == "POST" and form.is_valid():
        ref = uuid.uuid4().hex
        pay_obj = Payment.objects.create(user=request.user, amount=settings.SUBSCRIPTION_PRICE,
                                         operator=form.cleaned_data["operator"], phone=form.cleaned_data["phone"], reference=ref)
        if settings.DEBUG and not settings.PAY_USER:
            _apply(pay_obj)  # simulation locale uniquement
            messages.success(request, "Paiement simulé (mode développement).")
            return redirect("accounts:dashboard")
        try:
            pay_obj.provider_ref = providers.collect(pay_obj.amount, pay_obj.phone, ref, "Abonnement MetalLink 1 mois")
            pay_obj.save(update_fields=["provider_ref"])
        except providers.ProviderError:
            pay_obj.status = "failed"
            pay_obj.save(update_fields=["status"])
            messages.error(request, "Le service de paiement est indisponible. Réessayez plus tard.")
            return redirect("billing:pay")
        return render(request, "billing/waiting.html", {"payment": pay_obj})
    return render(request, "billing/pay.html", {"form": form, "profile": p, "history": request.user.payments.all()[:10]})


@login_required
def payment_status(request, reference):
    pay_obj = get_object_or_404(Payment, reference=reference, user=request.user)
    _refresh(pay_obj)
    return JsonResponse({"status": pay_obj.status})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def webhook(request):
    """Le contenu recu n'est jamais cru : on re-interroge l'agregateur."""
    if not settings.PAY_WEBHOOK_KEY or not hmac.compare_digest(request.GET.get("key", ""), settings.PAY_WEBHOOK_KEY):
        raise Http404
    ref = request.GET.get("external_reference") or request.GET.get("reference", "")
    try:
        pay_obj = Payment.objects.get(reference=ref[:40])
    except Payment.DoesNotExist:
        return HttpResponse(status=204)
    _refresh(pay_obj)
    return HttpResponse("ok")
