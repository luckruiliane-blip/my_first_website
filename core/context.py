from django.conf import settings


def site(request):
    return {
        "SUPPORT_WHATSAPP": settings.SUPPORT_WHATSAPP,
        "SUPPORT_EMAIL": settings.SUPPORT_EMAIL,
        "GOOGLE_VERIFY": settings.GOOGLE_SITE_VERIFICATION,
        "USE_COMPILED_CSS": settings.USE_COMPILED_CSS,
        "IMAGES": settings.IMAGES,
        "PRICE": settings.SUBSCRIPTION_PRICE,
        "TRIAL_DAYS": settings.TRIAL_DAYS,
    }
