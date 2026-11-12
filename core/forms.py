from django import forms

from . import validators as v

BASE = "w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 placeholder-slate-400 focus:border-orange-500 focus:ring-2 focus:ring-orange-200 outline-none transition"


class SafeCharField(forms.CharField):
    def __init__(self, *args, multiline=False, **kwargs):
        self.multiline = multiline
        kwargs.setdefault("strip", False)
        super().__init__(*args, **kwargs)
        self.widget.attrs["data-safe"] = "multi" if multiline else "line"
        if self.max_length:
            self.widget.attrs["maxlength"] = self.max_length

    def to_python(self, value):
        value = super().to_python(value)
        return v.clean_text(value, self.multiline)

    def validate(self, value):
        super().validate(value)
        if value:
            (v.validate_safe_multiline if self.multiline else v.validate_safe_text)(value)


class SafeEmailField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 120)
        super().__init__(*args, **kwargs)
        self.widget = forms.EmailInput(attrs={"data-safe": "email", "autocomplete": "email", "maxlength": 120})

    def to_python(self, value):
        return (super().to_python(value) or "").strip().lower()

    def validate(self, value):
        super().validate(value)
        if value:
            v.validate_safe_email(value)


class PhoneField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 16)
        super().__init__(*args, **kwargs)
        self.widget = forms.TextInput(attrs={"data-safe": "phone", "inputmode": "tel", "placeholder": "6 70 00 00 00", "maxlength": 16})

    def to_python(self, value):
        value = super().to_python(value)
        return v.normalize_phone(value) if value else ""


class StyledMixin:
    """Applique le style Tailwind et ajoute un champ piege anti-robots."""
    honeypot = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.honeypot:
            self.fields["website"] = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))
        for name, f in self.fields.items():
            w = f.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs["class"] = "h-4 w-4 rounded border-slate-300 text-orange-600"
            elif isinstance(w, forms.RadioSelect):
                continue
            elif name != "website":
                w.attrs["class"] = (w.attrs.get("class", "") + " " + BASE).strip()

    def clean(self):
        data = super().clean()
        if self.honeypot and self.data.get("website"):
            raise forms.ValidationError("Requête refusée.")
        return data
