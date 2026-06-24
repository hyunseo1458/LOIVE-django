#!/usr/bin/env bash

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Running migrations..."
python manage.py migrate --no-input

echo "==> Loading data..."
python -X utf8 -c "
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from activities.models import Activity, Category
from accounts.models import User
from allauth.socialaccount.models import SocialApp
from allauth.account.models import EmailAddress
from django.contrib.sites.models import Site

# 1. Force load fixture data (replaces all activity/category data)
print('Clearing old data...')
from django.core.management import call_command
from activities.models import ActivitySlot, ActivityImage, Course
from core.models import Wishlist
Wishlist.objects.all().delete()
Course.objects.all().delete()
ActivitySlot.objects.all().delete()
ActivityImage.objects.all().delete()
Activity.objects.all().delete()
Category.objects.all().delete()
print('Loading fixture...')
call_command('loaddata', 'fixtures/data.json', verbosity=1)
print(f'Loaded: {Activity.objects.count()} activities, {Category.objects.count()} categories')

# 2. Create admin if not exists
if not User.objects.filter(username='hyunseo1458').exists():
    u = User.objects.create_superuser('hyunseo1458', 'hyunseo1458@gmail.com', 'qwer0814!!')
    u.role = 'admin'
    u.save()
    print('Admin created')

# 3. Verify email for Google OAuth
user = User.objects.filter(email='hyunseo1458@gmail.com').first()
if user:
    EmailAddress.objects.update_or_create(
        user=user, email='hyunseo1458@gmail.com',
        defaults={'verified': True, 'primary': True}
    )

# 4. Setup Google OAuth
client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
if client_id:
    site = Site.objects.get_current()
    app, created = SocialApp.objects.get_or_create(
        provider='google',
        defaults={'name': 'Google', 'client_id': client_id, 'secret': os.environ.get('GOOGLE_CLIENT_SECRET', '')}
    )
    if not created:
        app.client_id = client_id
        app.secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
        app.save()
    app.sites.add(site)
    print('Google OAuth ready')
"

echo "==> Starting server..."
exec gunicorn config.wsgi:application
