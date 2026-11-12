from django.conf import settings
from django.db import models


class Payment(models.Model):
    OPERATORS = [("mtn", "MTN Mobile Money"), ("orange", "Orange Money")]
    STATUS = [("pending", "En attente"), ("success", "Réussi"), ("failed", "Échoué")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments")
    amount = models.PositiveIntegerField()
    operator = models.CharField(max_length=10, choices=OPERATORS)
    phone = models.CharField(max_length=12)
    reference = models.CharField(max_length=40, unique=True)
    provider_ref = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
