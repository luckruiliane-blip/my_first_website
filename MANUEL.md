# MetalLink : manuel d'installation et d'utilisation

Plateforme de mise en relation clients / soudeurs du Littoral (Cameroun).
Pile : Django 5, MySQL, HTML, Tailwind CSS, JavaScript.

## 1. Ce que fait le site

- **Clients** : recherche par ville et type de travail (sans rechargement), contact WhatsApp, prise de rendez-vous, demande de devis, suivi dans « Mon espace ».
- **Soudeurs** : fiche avec lieu d'exercice, téléphone et WhatsApp (affichés sur la fiche), services, réception des rendez-vous et devis (réponse avec un prix).
- **Abonnement** : 60 jours gratuits, puis 5 000 FCFA **par mois** par MTN MoMo ou Orange Money. Accès expiré = fiche masquée, plus de publication ni de mise à jour. Un paiement s'ajoute au temps restant.
- **Service client** : formulaire de contact + lien WhatsApp (visibles dans le pied de page).
- **Vous (super administrateur)** : tableau de pilotage (chiffres, inscrits, paiements, messages) et administration complète. Chaque nouvelle inscription, rendez-vous, devis, message ou paiement vous est envoyé par e-mail (et Telegram si vous le configurez).

## 2. Installation locale (test)

**Windows, méthode la plus simple : double-cliquez sur `demarrer.bat`.** Il installe tout, crée la base de test, vous demande votre e-mail et votre mot de passe de super administrateur, puis lance le site sur http://127.0.0.1:8000. (Python doit être installé, avec la case « Add Python to PATH » cochée.)

Méthode manuelle :
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Dans `.env`, pour tester sans MySQL : `DJANGO_DEBUG=1`, `DB_ENGINE=sqlite`, `OWNER_EMAIL=votre@email`.
```bash
python manage.py makemigrations accounts market billing
python manage.py migrate
python manage.py creer_superadmin     # crée votre compte (adresse OWNER_EMAIL)
python manage.py test                 # lance les tests de filtrage
python manage.py runserver
```
Le fichier `requirements.txt` contient `mysqlclient` (pour MySQL). Sous Windows, installez d'abord les outils de compilation ou utilisez `DB_ENGINE=sqlite` pour les tests.

## 3. Mise en ligne (serveur Ubuntu)

1. **Louer un serveur (VPS)** Ubuntu 22.04/24.04 chez un hébergeur (OVH, Hetzner, Contabo…). Pointer le nom de domaine vers l'IP du serveur (enregistrements DNS A pour `@` et `www`).
2. **Nom de domaine** : à acheter chez un registraire de votre choix (.com, .net, ou .cm via un registraire agréé). Le nom « metallink.cm » est un exemple : vérifiez sa disponibilité. Un nom de domaine ne peut pas être réservé à votre place.
3. Installer : `sudo apt install python3-venv nginx mysql-server libmysqlclient-dev build-essential pkg-config certbot python3-certbot-nginx nodejs npm`
4. **MySQL** : `sudo mysql < deploy/mysql_setup.sql` (changer d'abord le mot de passe dans le fichier). Le compte créé n'a des droits que sur la base `metallink`.
5. Copier le projet dans `/srv/metallink`, créer le `venv`, `pip install -r requirements-prod.txt`.
6. Remplir `.env` : `DJANGO_DEBUG=0`, une `DJANGO_SECRET_KEY` longue (générer avec `python -c "import secrets;print(secrets.token_urlsafe(60))"`), `ALLOWED_HOSTS`, les accès MySQL, `ADMIN_PATH` (adresse secrète de votre choix), `OWNER_EMAIL`.
7. **CSS compilé** (recommandé en production) : `npm install && npm run build:css`, puis mettre `USE_COMPILED_CSS=1`. Les règles de sécurité du navigateur deviennent plus strictes.
8. Initialiser :
```bash
python manage.py makemigrations accounts market billing
python manage.py migrate
python manage.py createcachetable
python manage.py collectstatic --noinput
python manage.py creer_superadmin
python manage.py check --deploy
```
9. Copier `deploy/metallink.service` dans `/etc/systemd/system/`, puis `sudo systemctl enable --now metallink`.
10. Copier `deploy/nginx.conf` dans `/etc/nginx/sites-available/`, l'activer, adapter le domaine, puis `sudo certbot --nginx -d votredomaine.com -d www.votredomaine.com` (HTTPS gratuit).

## 3 bis. Mise en ligne simple avec PythonAnywhere (sans serveur à gérer)

PythonAnywhere (pythonanywhere.com) héberge Django et MySQL, paiement en dollars par carte. Un nom de domaine personnalisé nécessite un compte payant.
1. Créez un compte, onglet **Files** : envoyez `metallink.zip`, puis dans **Consoles > Bash** : `unzip metallink.zip`.
2. `cd metallink && python3 -m venv ~/venv && source ~/venv/bin/activate && pip install -r requirements.txt`
3. Onglet **Databases** : créez un mot de passe MySQL et la base `VOTRENOM$metallink`.
4. Créez `.env` (copie de `.env.example`) avec `DJANGO_DEBUG=0`, une `DJANGO_SECRET_KEY`, `ALLOWED_HOSTS=VOTRENOM.pythonanywhere.com`, `DB_NAME=VOTRENOM$metallink`, `DB_USER=VOTRENOM`, `DB_HOST=VOTRENOM.mysql.pythonanywhere-services.com`, `OWNER_EMAIL`, `ADMIN_PATH`, `TRUST_PROXY=0`.
5. Console : `python manage.py makemigrations accounts market billing && python manage.py migrate && python manage.py createcachetable && python manage.py collectstatic --noinput && python manage.py creer_superadmin`
6. Onglet **Web** : « Add a new web app », Manual configuration, Python 3.12. Renseignez le dossier du code, le virtualenv `~/venv`, et dans le fichier WSGI pointez vers `config.wsgi` (ajoutez le dossier du projet à `sys.path`, `DJANGO_SETTINGS_MODULE=config.settings`). Ajoutez le fichier statique : URL `/static/` vers `.../staticfiles`.
7. Cliquez **Reload** : le site est en ligne en HTTPS sur `VOTRENOM.pythonanywhere.com`. Ensuite, liez votre nom de domaine depuis l'onglet Web.

## 4. Votre espace administrateur

- Connectez-vous sur la page **Connexion** normale avec votre adresse OWNER_EMAIL.
- Tableau de pilotage : `https://votredomaine/<ADMIN_PATH>/tableau/`
- Administration complète (utilisateurs, soudeurs, paiements, messages, suspension, badge « Vérifié ») : `https://votredomaine/<ADMIN_PATH>/`
- Pour toute autre personne (connectée ou non), ces adresses répondent « page introuvable ». Le contrôle se fait côté serveur à chaque requête : compte actif, super administrateur, membre du personnel ET adresse e-mail égale à `OWNER_EMAIL`. Option : `ADMIN_ALLOWED_IPS` pour n'autoriser que vos adresses IP.
- Notifications : renseignez `ADMIN_NOTIFY_EMAIL` et le serveur SMTP. Pour Telegram : créez un bot avec @BotFather et renseignez `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID`.

## 5. Paiement MTN MoMo / Orange Money

Le code utilise un agrégateur (modèle CamPay : demande de confirmation sur le téléphone du payeur, puis vérification serveur à serveur). Étapes :
1. Ouvrir un compte marchand chez l'agrégateur (CamPay, Notch Pay ou équivalent) et obtenir les identifiants API.
2. Renseigner `PAY_BASE_URL`, `PAY_USER`, `PAY_PASSWORD`, `PAY_WEBHOOK_KEY`.
3. Déclarer chez l'agrégateur l'adresse de notification : `https://votredomaine/paiement/retour-agregateur/?key=VOTRE_PAY_WEBHOOK_KEY`.
4. **Vérifier les chemins et champs de l'API dans la documentation de l'agrégateur** (fichier `billing/providers.py`) et faire un essai réel de 5 000 FCFA avant l'ouverture. Cette partie n'a pas pu être testée avec de vrais identifiants.

Sécurité du paiement : aucun code secret Mobile Money n'est saisi sur le site ; l'accès n'est accordé qu'après confirmation de l'agrégateur (le contenu reçu par notification n'est jamais cru tel quel) ; un paiement ne peut prolonger l'accès qu'une seule fois.

## 6. Sécurité en place

- **Formulaires** : seules les lettres (accents compris), chiffres et espaces sont acceptés dans les champs texte ; filtrage en direct dans le navigateur ET contrôle obligatoire côté serveur ET contrôle au niveau des modèles. Téléphone : chiffres uniquement (numéro camerounais). E-mail : caractères autorisés uniquement. Les mots de passe ne sont pas filtrés (ils doivent pouvoir contenir des symboles), mais sont chiffrés avec Argon2.
- **Base de données** : requêtes paramétrées (pas d'injection SQL), compte MySQL à droits limités, mode strict, utf8mb4.
- **Comptes** : un seul compte par e-mail (contrainte unique en base, insensible à la casse), mot de passe de 10 caractères minimum, blocage temporaire après des essais répétés.
- **Réseau et navigateur** : HTTPS forcé, HSTS, cookies sécurisés, protection CSRF, en-têtes CSP, anti-clickjacking, politique de référent.
- **Anti-robots** : limitation de débit par IP, champ piège invisible.
- Recommandé en plus : Cloudflare (WAF, Turnstile), pare-feu `ufw` (ports 22/80/443), `fail2ban`, sauvegardes MySQL chiffrées (`mysqldump` quotidien copié hors du serveur), mises à jour système régulières, double authentification pour votre compte.

## 7. Images

Les images du site (bannière, cartes) sont chargées depuis un autre site (loremflickr.com, photos par mot-clé). Pour changer de source, modifiez le dictionnaire `IMAGES` dans `config/settings.py` et ajoutez le domaine à `img-src` dans `core/middleware.py`. Pour des photos de qualité constante, préférez votre propre hébergeur d'images.

## 8. Maintenance courante

- Sauvegarde : `mysqldump -u metallink_user -p metallink > sauvegarde.sql`
- Mise à jour du code : remplacer les fichiers, puis `migrate`, `collectstatic`, `sudo systemctl restart metallink`.
- Modifier le prix ou les durées : `SUBSCRIPTION_PRICE`, `TRIAL_DAYS`, `SUBSCRIPTION_DAYS` dans `config/settings.py`.
- Les textes « Conditions d'utilisation » et « Confidentialité » sont des modèles : à faire valider par un juriste.

## 9. Application mobile avec Capacitor (Android / iOS)

Le site Django tourne sur un serveur : l'application Capacitor est une « coque » qui charge votre site en ligne dans une vraie application installable. **Le site doit donc être publié en HTTPS avant de construire l'application.** Le dossier `capacitor/` est déjà prêt (configuration, icônes, écran de démarrage).

**À installer** : Node.js (version LTS) et Android Studio. Pour iOS : un Mac, Xcode et un compte Apple Developer (environ 99 $ par an). Compte Google Play : environ 25 $, une seule fois.

1. Ouvrez `capacitor/capacitor.config.json` et remplacez `VOTRE-DOMAINE.com` (dans `url` et dans `allowNavigation`) par votre vrai domaine. Vous pouvez aussi changer `appId`.
2. Dans un terminal :
```bash
cd capacitor
npm install
npx cap add android
npm run icones
npx cap sync
npx cap open android
```
3. Dans Android Studio : **Build > Build Bundle(s) / APK(s) > Build APK(s)** pour un fichier à installer sur un téléphone de test. Pour le Play Store : **Generate Signed Bundle (.aab)**. Gardez précieusement le fichier de signature et son mot de passe : sans eux, vous ne pourrez plus mettre l'application à jour.
4. iOS (sur Mac) : `npx cap add ios`, `npx cap sync`, `npx cap open ios`, puis publication via Xcode.

**Points à connaître**
- L'application nécessite Internet. Hors connexion, elle affiche une page « Réessayer ».
- Apple refuse souvent les applications qui ne sont qu'un site dans une coque (règle 4.2). Google est plus souple mais demande aussi une vraie valeur. Prévoyez d'ajouter plus tard des fonctions natives (notifications, etc.) pour renforcer la candidature.
- Paiement : Google Play impose son propre système de paiement pour certains services numériques vendus dans l'application. Vérifiez la politique « Google Play Payments » pour l'abonnement soudeur avant de publier sur le store. Une alternative sans store : distribuer le fichier APK directement.
- Le site est aussi **installable sans store** : sur téléphone, menu du navigateur > « Ajouter à l'écran d'accueil » (le manifeste est inclus).
- Je n'ai pas pu compiler l'application dans mon environnement : testez-la sur un téléphone avant de la publier.

## 10. Être trouvé sur Google (référencement)

**Déjà en place dans le site** : titres et descriptions pour chaque page, balises de partage, données structurées « entreprise locale » sur chaque fiche soudeur (sans numéro de téléphone), `sitemap.xml` automatique (pages et fiches visibles), `robots.txt` qui exclut les espaces privés, pages privées en `noindex`.

**À faire après la mise en ligne**
1. Créez un compte sur **search.google.com/search-console** et ajoutez votre site (« Préfixe de l'URL »).
2. Choisissez la vérification par **balise HTML** : copiez la valeur de `content`, collez-la dans `.env` à la ligne `GOOGLE_SITE_VERIFICATION=`, redémarrez le site, puis cliquez sur Valider.
3. Dans « Sitemaps », ajoutez `sitemap.xml`. Dans « Inspection de l'URL », demandez l'indexation de la page d'accueil.
4. Faites la même chose sur **Bing Webmaster Tools**.
5. Créez une fiche **Google Business Profile** pour MetalLink et partagez le lien du site sur Facebook, WhatsApp et dans des groupes de métiers.
6. Encouragez les soudeurs à remplir leur description et leurs services : plus de contenu réel, meilleur référencement (mots comme « soudeur Douala », « portail métallique »).

Les premières pages apparaissent en général après quelques jours à quelques semaines. Personne ne peut garantir une première place sur Google.
