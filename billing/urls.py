from django.urls import path

from . import views

app_name = "billing"
urlpatterns = [
    path("abonnement/", views.pay, name="pay"),
    path("abonnement/statut/<str:reference>/", views.payment_status, name="status"),
    path("paiement/retour-agregateur/", views.webhook, name="webhook"),
]
