from django.contrib import admin

from .models import Appointment, ArtisanProfile, ContactClick, Quote, Service, SupportMessage

admin.site.register([ArtisanProfile, Service, Appointment, Quote, SupportMessage, ContactClick])
