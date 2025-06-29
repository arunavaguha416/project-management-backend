# Geological Data Store Backend
 Geological Data Store Website Project

    Creating a Virtual Env
    python -m venv venv

    Activating Virtual Env
    .\venv\Scripts\activate

    Insatll Django
    pip install Django

    Check Django Version
    python -m django --version

    Creating a Django Project
    python -m django startproject cams_django . . operator indicates current Directory

    Run a Dgnago project
    python manage.py runserver

    Creating an App
    python manage.py startapp auth

    creating requirements.txt
    pip freeze > requirements.txt

    install All the Dependency
    pip install -r requirements.txt

    install django rest framework
    Activate the virtual env using the .\venv\Scripts\activate the run the followin command pip install djangorestframework

    install django dotenv
    pip install django-dotenv

    Instal mysql Client
    pip install mysqlclient

    Install JWT Token
    pip install djangorestframework-simplejwt add the following to settings.py 'rest_framework_simplejwt', 'rest_framework_simplejwt.token_blacklist'

    Generate Migration
    python manage.py makemigrations

    Run the migration
    python manage.py migrate

    To load language data
    python manage.py loaddata authentication/seed/language.json

    To load Zone data
    python manage.py loaddata species/seed/zone.json