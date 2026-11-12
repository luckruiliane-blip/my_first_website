import json
import threading
import urllib.request

from django.conf import settings
from django.core.mail import send_mail


def _telegram(text):
    if not (settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID):
        return
    try:
        data = json.dumps({"chat_id": settings.TELEGRAM_CHAT_ID, "text": text}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=8)
    except Exception:
        pass


def notify_admin(subject, lines):
    body = "\n".join(lines)

    def work():
        if settings.ADMIN_NOTIFY_EMAIL:
            send_mail(f"[MetalLink] {subject}", body, None, [settings.ADMIN_NOTIFY_EMAIL], fail_silently=True)
        _telegram(f"{subject}\n{body}")

    threading.Thread(target=work, daemon=True).start()
