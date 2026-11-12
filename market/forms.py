import datetime

from django import forms
from django.utils import timezone

from core.forms import SafeCharField, SafeEmailField, StyledMixin
from core.forms import PhoneField
from .models import CATEGORIES, CITIES, Appointment, ArtisanProfile, Quote, Service, SupportMessage


class ProfileForm(StyledMixin, forms.ModelForm):
    business_name = SafeCharField(label="Nom de l'atelier", max_length=80)
    location = SafeCharField(label="Lieu d'exercice (quartier, rue)", max_length=120)
    landmark = SafeCharField(label="Point de repère", max_length=120, required=False)
    phone = PhoneField(label="Téléphone")
    whatsapp = PhoneField(label="Numéro WhatsApp")
    bio = SafeCharField(label="Présentation", max_length=600, multiline=True, required=False, widget=forms.Textarea(attrs={"rows": 4}))

    class Meta:
        model = ArtisanProfile
        fields = ["business_name", "city", "location", "landmark", "phone", "whatsapp", "years_experience", "bio"]


class ServiceForm(StyledMixin, forms.ModelForm):
    title = SafeCharField(label="Titre du service", max_length=80)
    description = SafeCharField(label="Description", max_length=600, multiline=True, widget=forms.Textarea(attrs={"rows": 4}))

    class Meta:
        model = Service
        fields = ["title", "category", "description", "price_from", "is_published"]


class AppointmentForm(StyledMixin, forms.ModelForm):
    work_place = SafeCharField(label="Lieu du travail (quartier, rue)", max_length=120)
    note = SafeCharField(label="Précisions", max_length=500, multiline=True, required=False, widget=forms.Textarea(attrs={"rows": 3}))

    class Meta:
        model = Appointment
        fields = ["service", "date", "time", "work_place", "note"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"}), "time": forms.TimeInput(attrs={"type": "time"})}

    def __init__(self, *a, profile=None, **kw):
        super().__init__(*a, **kw)
        self.fields["service"].queryset = Service.objects.filter(profile=profile, is_published=True)
        self.fields["service"].required = False
        self.fields["date"].widget.attrs["min"] = timezone.localdate().isoformat()

    def clean_date(self):
        d = self.cleaned_data["date"]
        today = timezone.localdate()
        if d < today or d > today + datetime.timedelta(days=180):
            raise forms.ValidationError("Choisissez une date dans les 6 prochains mois.")
        return d


class QuoteForm(StyledMixin, forms.ModelForm):
    description = SafeCharField(label="Décrivez votre projet (dimensions, matériaux, usage)", max_length=800, multiline=True, widget=forms.Textarea(attrs={"rows": 5}))

    class Meta:
        model = Quote
        fields = ["category", "city", "description", "budget"]


class QuoteAnswerForm(StyledMixin, forms.ModelForm):
    answer_note = SafeCharField(label="Détails de votre offre", max_length=500, multiline=True, required=False, widget=forms.Textarea(attrs={"rows": 3}))

    class Meta:
        model = Quote
        fields = ["answer_price", "answer_note"]

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.fields["answer_price"].required = True
        self.fields["answer_price"].label = "Prix proposé (FCFA)"


class SupportForm(StyledMixin, forms.ModelForm):
    honeypot = True
    name = SafeCharField(label="Nom", max_length=80)
    email = SafeEmailField(label="Adresse e-mail")
    subject = SafeCharField(label="Sujet", max_length=100)
    message = SafeCharField(label="Message", max_length=1000, multiline=True, widget=forms.Textarea(attrs={"rows": 5}))

    class Meta:
        model = SupportMessage
        fields = ["name", "email", "subject", "message"]
