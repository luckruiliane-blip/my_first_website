from django.apps import apps
from django.db import transaction
from django.db.models.signals import post_save

from .notify import notify_admin


def _on_create(model_label, title, fmt):
    model = apps.get_model(model_label)

    def handler(sender, instance, created, **kw):
        if created:
            transaction.on_commit(lambda: notify_admin(title, fmt(instance)))

    post_save.connect(handler, sender=model, weak=False, dispatch_uid=f"notify_{model_label}")


_on_create("accounts.User", "Nouvelle inscription", lambda o: [
    f"Nom : {o.full_name}", f"E-mail : {o.email}", f"Téléphone : {o.phone}", f"Rôle : {o.role}"])
_on_create("market.ArtisanProfile", "Nouveau soudeur", lambda o: [
    f"Atelier : {o.business_name}", f"Ville : {o.city}", f"Lieu : {o.location}", f"WhatsApp : {o.whatsapp}"])
_on_create("market.Appointment", "Nouveau rendez-vous", lambda o: [
    f"Client : {o.client.full_name}", f"Soudeur : {o.profile.business_name}", f"Date : {o.date} {o.time}"])
_on_create("market.Quote", "Nouvelle demande de devis", lambda o: [
    f"Client : {o.client.full_name}", f"Soudeur : {o.profile.business_name}", f"Ville : {o.city}", f"Budget : {o.budget}"])
_on_create("market.SupportMessage", "Message au service client", lambda o: [
    f"De : {o.name} ({o.email})", f"Sujet : {o.subject}", o.message])
_on_create("billing.Payment", "Paiement initié", lambda o: [
    f"Utilisateur : {o.user.email}", f"Montant : {o.amount} FCFA", f"Opérateur : {o.operator}"])
