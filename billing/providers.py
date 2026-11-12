"""Client d'agregateur de paiement mobile (modele CamPay : collecte MTN MoMo / Orange Money).
Verifiez chemins et champs dans la documentation de votre agregateur avant la mise en ligne."""
import json
import urllib.request

from django.conf import settings
from django.core.cache import cache


class ProviderError(Exception):
    pass


def _call(method, path, payload=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Token {token}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(settings.PAY_BASE_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as exc:
        raise ProviderError(str(exc))


def _token():
    t = cache.get("pay_token")
    if t:
        return t
    res = _call("POST", "/token/", {"username": settings.PAY_USER, "password": settings.PAY_PASSWORD})
    t = res.get("token")
    if not t:
        raise ProviderError("Jeton refusé")
    cache.set("pay_token", t, 240)
    return t


def collect(amount, phone, reference, description):
    """Declenche la demande de confirmation sur le telephone du payeur."""
    res = _call("POST", "/collect/", {
        "amount": str(amount), "currency": "XAF", "from": phone,
        "description": description, "external_reference": reference,
    }, token=_token())
    return res.get("reference", "")


def status(provider_ref):
    """Retourne 'success', 'failed' ou 'pending' (toujours verifie aupres de l'agregateur)."""
    res = _call("GET", f"/transaction/{provider_ref}/", token=_token())
    s = str(res.get("status", "")).upper()
    return {"SUCCESSFUL": "success", "FAILED": "failed"}.get(s, "pending")
