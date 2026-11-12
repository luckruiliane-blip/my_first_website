"""Filtrage strict : seules les lettres (accents compris), les chiffres et les espaces passent."""
import re
import unicodedata

from django.core.exceptions import ValidationError

_L = "A-Za-zÀ-ÖØ-öø-ÿŒœ"
SAFE_LINE = re.compile(rf"^[{_L}0-9 ]+$")
SAFE_MULTI = re.compile(rf"^[{_L}0-9 \n]+$")
SAFE_EMAIL = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*@[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+(?:-[a-z0-9]+)*)+$")
MODEL_PHONE = re.compile(r"^2376[0-9]{8}$")

MSG_TEXT = "Caractères spéciaux interdits : utilisez uniquement des lettres, des chiffres et des espaces."


def clean_text(value, multiline=False):
    value = unicodedata.normalize("NFC", (value or "")).replace("\r\n", "\n").replace("\r", "\n")
    if multiline:
        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
    else:
        value = re.sub(r"\s+", " ", value)
    return value.strip()


def validate_safe_text(value):
    if not SAFE_LINE.match(value or ""):
        raise ValidationError(MSG_TEXT, code="special_chars")


def validate_safe_multiline(value):
    if not SAFE_MULTI.match(value or ""):
        raise ValidationError(MSG_TEXT, code="special_chars")


def validate_safe_email(value):
    if not SAFE_EMAIL.match((value or "").lower()) or len(value) > 120:
        raise ValidationError("Adresse e-mail invalide ou contenant des caractères interdits.", code="bad_email")


def normalize_phone(raw):
    digits = (raw or "").replace(" ", "")
    if not re.fullmatch(r"\+?[0-9]+", digits):
        raise ValidationError("Numéro invalide : chiffres uniquement (ex. 6 70 00 00 00).", code="bad_phone")
    digits = digits.lstrip("+")
    if digits.startswith("237"):
        digits = digits[3:]
    if not re.fullmatch(r"6[0-9]{8}", digits):
        raise ValidationError("Numéro camerounais invalide (9 chiffres commençant par 6).", code="bad_phone")
    return "237" + digits


def validate_phone(value):
    if not MODEL_PHONE.match(value or ""):
        raise ValidationError("Numéro camerounais invalide.", code="bad_phone")
