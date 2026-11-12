from django.urls import path

from . import views

app_name = "market"
urlpatterns = [
    path("", views.home, name="home"),
    path("soudeurs/", views.artisan_list, name="list"),
    path("soudeurs/<int:pk>/", views.artisan_detail, name="detail"),
    path("soudeurs/<int:pk>/rendez-vous/", views.appointment_create, name="appointment"),
    path("soudeurs/<int:pk>/devis/", views.quote_create, name="quote"),
    path("api/soudeurs/", views.api_artisans, name="api_list"),
    path("api/soudeurs/<int:pk>/contact/", views.api_contact, name="api_contact"),
    path("mon-profil/", views.profile_edit, name="profile"),
    path("mes-services/nouveau/", views.service_edit, name="service_new"),
    path("mes-services/<int:pk>/", views.service_edit, name="service_edit"),
    path("mes-services/<int:pk>/supprimer/", views.service_delete, name="service_delete"),
    path("rendez-vous/<int:pk>/<str:status>/", views.appointment_status, name="appointment_status"),
    path("devis/<int:pk>/repondre/", views.quote_answer, name="quote_answer"),
    path("devis/<int:pk>/<str:decision>/", views.quote_decide, name="quote_decide"),
    path("contact/", views.support, name="support"),
    path("legal/<str:page>/", views.legal, name="legal"),
]
