@echo off
chcp 65001 >nul
echo === MetalLink : demarrage local ===
where python >nul 2>nul || (echo Python n'est pas installe. Installez-le depuis python.org puis relancez. & pause & exit /b)
if not exist venv ( python -m venv venv )
call venv\Scripts\activate
pip install -r requirements.txt
if not exist .env (
  copy .env.example .env >nul
  powershell -Command "(Get-Content .env) -replace 'DJANGO_DEBUG=0','DJANGO_DEBUG=1' -replace 'DB_ENGINE=mysql','DB_ENGINE=sqlite' -replace 'ALLOWED_HOSTS=.*','ALLOWED_HOSTS=localhost,127.0.0.1' | Set-Content .env"
  echo.
  set /p MAIL=Tapez votre adresse e-mail de super administrateur : 
  powershell -Command "(Get-Content .env) -replace 'OWNER_EMAIL=vous@exemple.com','OWNER_EMAIL=%MAIL%' -replace 'ADMIN_NOTIFY_EMAIL=vous@exemple.com','ADMIN_NOTIFY_EMAIL=%MAIL%' | Set-Content .env"
)
python manage.py makemigrations accounts market billing
python manage.py migrate
python manage.py creer_superadmin
echo.
echo Ouvrez http://127.0.0.1:8000 dans votre navigateur (Ctrl+C pour arreter).
python manage.py runserver
