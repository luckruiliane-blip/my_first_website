from django.core.exceptions import ValidationError
from django.test import TestCase

from core import validators as v


class FilterTests(TestCase):
    def test_text_rejects_special_characters(self):
        for bad in ["Jean!", "a;b", "x&y", "é\"à", "<script>", "a--b", "x'y", "ok.ok", "(test)", "a=b"]:
            with self.assertRaises(ValidationError, msg=bad):
                v.validate_safe_text(bad)

    def test_text_accepts_letters_digits_spaces(self):
        for good in ["Jean Paul", "Atelier Étoile 2", "Éric Nkoulou"]:
            v.validate_safe_text(good)

    def test_phone(self):
        self.assertEqual(v.normalize_phone("6 70 00 00 00"), "237670000000")
        self.assertEqual(v.normalize_phone("+237670000000"), "237670000000")
        with self.assertRaises(ValidationError):
            v.normalize_phone("12;34")

    def test_email(self):
        v.validate_safe_email("jean.paul@gmail.com")
        with self.assertRaises(ValidationError):
            v.validate_safe_email("jean'--@x.com")


class AdminShieldTests(TestCase):
    def test_admin_hidden_from_visitors(self):
        from django.conf import settings
        self.assertEqual(self.client.get(f"/{settings.ADMIN_PATH}/").status_code, 404)
        self.assertEqual(self.client.get(f"/{settings.ADMIN_PATH}/tableau/").status_code, 404)
        self.assertEqual(self.client.get("/admin/").status_code, 404)


class SeoTests(TestCase):
    def test_robots_and_sitemap(self):
        from django.conf import settings
        r = self.client.get("/robots.txt")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Sitemap:", r.content.decode())
        self.assertNotIn(settings.ADMIN_PATH, r.content.decode())
        self.assertEqual(self.client.get("/sitemap.xml").status_code, 200)
