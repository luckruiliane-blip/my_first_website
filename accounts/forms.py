from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from core.forms import PhoneField, SafeCharField, SafeEmailField, StyledMixin
from market.models import CITIES, ArtisanProfile

User = get_user_model()


class RegisterForm(StyledMixin, forms.Form):
    honeypot = True
    role = forms.ChoiceField(choices=[("client", "Je cherche un soudeur"), ("artisan", "Je suis soudeur")], widget=forms.RadioSelect)
    full_name = SafeCharField(label="Nom complet", max_length=80)
    email = SafeEmailField(label="Adresse e-mail")
    phone = PhoneField(label="Téléphone")
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}), max_length=128)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}), max_length=128)
    # Champs soudeur
    business_name = SafeCharField(label="Nom de l'atelier", max_length=80, required=False)
    city = forms.ChoiceField(label="Ville", choices=[("", "Choisir")] + CITIES, required=False)
    location = SafeCharField(label="Lieu d'exercice (quartier, rue)", max_length=120, required=False)
    whatsapp = PhoneField(label="Numéro WhatsApp", required=False)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un compte existe déjà avec cette adresse e-mail.")
        return email

    def clean(self):
        data = super().clean()
        if data.get("password1") != data.get("password2"):
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        elif data.get("password1"):
            try:
                validate_password(data["password1"])
            except forms.ValidationError as e:
                self.add_error("password1", e)
        if data.get("role") == "artisan":
            for f in ("business_name", "city", "location"):
                if not data.get(f):
                    self.add_error(f, "Champ obligatoire pour un soudeur.")
        return data

    @transaction.atomic
    def save(self):
        d = self.cleaned_data
        user = User.objects.create_user(email=d["email"], password=d["password1"], full_name=d["full_name"], phone=d["phone"], role=d["role"])
        if d["role"] == "artisan":
            ArtisanProfile.objects.create(
                user=user, business_name=d["business_name"], city=d["city"], location=d["location"],
                phone=d["phone"], whatsapp=d.get("whatsapp") or d["phone"])
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Adresse e-mail", max_length=120, widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    password = forms.CharField(label="Mot de passe", max_length=128, widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))
    error_messages = {"invalid_login": "Identifiants incorrects.", "inactive": "Compte désactivé."}

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        from core.forms import BASE
        for f in self.fields.values():
            f.widget.attrs["class"] = BASE

    def clean_username(self):
        return self.cleaned_data["username"].strip().lower()
