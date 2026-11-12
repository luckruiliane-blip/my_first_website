from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.security import allow, client_ip, throttled
from market.models import Appointment, Quote

from .forms import LoginForm, RegisterForm


@throttled("register", limit=8, window=3600)
@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = RegisterForm(request.POST or None, initial={"role": request.GET.get("role", "client")})
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Bienvenue sur MetalLink ! Votre compte est créé.")
        return redirect("accounts:dashboard")
    return render(request, "accounts/register.html", {"form": form})


class SafeLoginView(LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def post(self, request, *a, **kw):
        email = (request.POST.get("username") or "").strip().lower()[:120]
        if not allow(f"login:{client_ip(request)}:{email}", 6, 900) or not allow(f"loginip:{client_ip(request)}", 30, 900):
            messages.error(request, "Trop de tentatives. Réessayez dans 15 minutes.")
            return redirect("accounts:login")
        return super().post(request, *a, **kw)


@login_required
def dashboard(request):
    u = request.user
    if u.role == "artisan" and hasattr(u, "profile"):
        p = u.profile
        ctx = {
            "profile": p,
            "services": p.services.all(),
            "appointments": p.appointments.select_related("client", "service")[:30],
            "quotes": p.quotes.select_related("client")[:30],
            "now": timezone.now(),
        }
        return render(request, "accounts/dashboard_artisan.html", ctx)
    ctx = {
        "appointments": Appointment.objects.filter(client=u).select_related("profile", "service")[:30],
        "quotes": Quote.objects.filter(client=u).select_related("profile")[:30],
    }
    return render(request, "accounts/dashboard_client.html", ctx)
