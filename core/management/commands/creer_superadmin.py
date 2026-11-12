import getpass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crée (ou met à jour) l'unique compte super administrateur défini par OWNER_EMAIL."

    def handle(self, *args, **opts):
        User = get_user_model()
        email = settings.OWNER_EMAIL
        if not email:
            raise CommandError("Renseignez OWNER_EMAIL dans le fichier .env avant de continuer.")
        if User.objects.filter(is_superuser=True).exclude(email=email).exists():
            raise CommandError("Un autre super administrateur existe déjà. Un seul est autorisé.")
        name = input("Votre nom complet (lettres et espaces) : ").strip() or "Administrateur"
        pw = getpass.getpass("Mot de passe (10 caractères minimum) : ")
        if pw != getpass.getpass("Confirmez le mot de passe : "):
            raise CommandError("Les mots de passe ne correspondent pas.")
        try:
            validate_password(pw)
        except ValidationError as e:
            raise CommandError(" ".join(e.messages))
        user = User.objects.filter(email=email).first()
        if user:
            user.set_password(pw)
            user.is_staff = user.is_superuser = True
            user.role = "admin"
            user.save()
        else:
            User.objects.create_superuser(email=email, password=pw, full_name=name)
        self.stdout.write(self.style.SUCCESS(f"Super administrateur prêt : {email}"))
