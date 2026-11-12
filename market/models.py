from datetime import timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from core.validators import validate_phone, validate_safe_multiline, validate_safe_text

CITIES = [(c, c) for c in [
    "Douala", "Edéa", "Nkongsamba", "Loum", "Mbanga", "Manjo", "Melong",
    "Penja", "Yabassi", "Dizangué", "Mouanko", "Dibombari", "Pouma",
]]
CATEGORIES = [
    ("portails", "Portails et portes"),
    ("grilles", "Grilles et fenêtres"),
    ("charpente", "Charpente métallique"),
    ("escaliers", "Escaliers et rampes"),
    ("mobilier", "Mobilier métallique"),
    ("reparation", "Réparation et soudure"),
    ("chantier", "Soudure sur chantier"),
    ("autre", "Autre travail"),
]


class ArtisanProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    business_name = models.CharField("atelier", max_length=80, validators=[validate_safe_text])
    city = models.CharField("ville", max_length=30, choices=CITIES)
    location = models.CharField("lieu d'exercice", max_length=120, validators=[validate_safe_text])
    landmark = models.CharField("point de repère", max_length=120, blank=True, validators=[validate_safe_text])
    phone = models.CharField(max_length=12, validators=[validate_phone])
    whatsapp = models.CharField(max_length=12, validators=[validate_phone])
    bio = models.TextField("présentation", max_length=600, blank=True, validators=[validate_safe_multiline])
    years_experience = models.PositiveSmallIntegerField("années d'expérience", default=0, validators=[MaxValueValidator(60)])
    trial_ends = models.DateTimeField(editable=False)
    paid_until = models.DateTimeField(null=True, blank=True)
    is_verified = models.BooleanField("vérifié", default=False)
    is_suspended = models.BooleanField("suspendu", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_verified", "-created_at"]

    def save(self, *a, **kw):
        if not self.trial_ends:
            self.trial_ends = timezone.now() + timedelta(days=settings.TRIAL_DAYS)
        super().save(*a, **kw)

    @property
    def access_until(self):
        return max(self.trial_ends, self.paid_until) if self.paid_until else self.trial_ends

    @property
    def has_access(self):
        return not self.is_suspended and self.access_until > timezone.now()

    @property
    def days_left(self):
        return max((self.access_until - timezone.now()).days, 0)

    @property
    def in_trial(self):
        return not self.paid_until and self.trial_ends > timezone.now()

    def extend(self, days):
        base = max(timezone.now(), self.access_until)
        self.paid_until = base + timedelta(days=days)
        self.save(update_fields=["paid_until"])

    def __str__(self):
        return self.business_name


class Service(models.Model):
    profile = models.ForeignKey(ArtisanProfile, on_delete=models.CASCADE, related_name="services")
    title = models.CharField("titre", max_length=80, validators=[validate_safe_text])
    category = models.CharField("catégorie", max_length=20, choices=CATEGORIES)
    description = models.TextField(max_length=600, validators=[validate_safe_multiline])
    price_from = models.PositiveIntegerField("prix à partir de (FCFA)", null=True, blank=True, validators=[MaxValueValidator(50_000_000)])
    is_published = models.BooleanField("publié", default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class Appointment(models.Model):
    STATUS = [("pending", "En attente"), ("confirmed", "Confirmé"), ("declined", "Refusé"), ("done", "Terminé"), ("cancelled", "Annulé")]
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments")
    profile = models.ForeignKey(ArtisanProfile, on_delete=models.CASCADE, related_name="appointments")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    work_place = models.CharField("lieu du travail", max_length=120, validators=[validate_safe_text])
    note = models.TextField(max_length=500, blank=True, validators=[validate_safe_multiline])
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Quote(models.Model):
    STATUS = [("new", "Nouveau"), ("answered", "Répondu"), ("accepted", "Accepté"), ("refused", "Refusé")]
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quotes")
    profile = models.ForeignKey(ArtisanProfile, on_delete=models.CASCADE, related_name="quotes")
    category = models.CharField(max_length=20, choices=CATEGORIES)
    city = models.CharField(max_length=30, choices=CITIES)
    description = models.TextField(max_length=800, validators=[validate_safe_multiline])
    budget = models.PositiveIntegerField("budget (FCFA)", null=True, blank=True, validators=[MaxValueValidator(500_000_000)])
    status = models.CharField(max_length=10, choices=STATUS, default="new")
    answer_price = models.PositiveIntegerField(null=True, blank=True, validators=[MaxValueValidator(500_000_000)])
    answer_note = models.TextField(max_length=500, blank=True, validators=[validate_safe_multiline])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class SupportMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=80, validators=[validate_safe_text])
    email = models.CharField(max_length=120)
    subject = models.CharField(max_length=100, validators=[validate_safe_text])
    message = models.TextField(max_length=1000, validators=[validate_safe_multiline])
    handled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ContactClick(models.Model):
    profile = models.ForeignKey(ArtisanProfile, on_delete=models.CASCADE, related_name="clicks")
    created_at = models.DateTimeField(auto_now_add=True)
