from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "amount", "operator", "status", "created_at")
    list_filter = ("status", "operator")
    readonly_fields = [f.name for f in Payment._meta.fields]
