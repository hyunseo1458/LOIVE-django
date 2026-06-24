#!/usr/bin/env bash

echo "==> Collecting static files..."
python manage.py collectstatic --no-input

echo "==> Running migrations..."
python manage.py migrate --no-input

echo "==> Setting up data..."
python -c "
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from activities.models import Activity, Category
from accounts.models import User
from allauth.socialaccount.models import SocialApp
from allauth.account.models import EmailAddress
from django.contrib.sites.models import Site

# 1. Check if we need to fetch places (no Google data yet)
google_count = Activity.objects.exclude(google_place_id='').exclude(google_place_id__isnull=True).count()
if google_count == 0:
    print('No Google Places data found - will fetch after server start')
    # Delete old seed data
    Activity.objects.all().delete()
    Category.objects.all().delete()

# 2. Create admin if not exists
if not User.objects.filter(username='hyunseo1458').exists():
    u = User.objects.create_superuser('hyunseo1458', 'hyunseo1458@gmail.com', 'qwer0814!!')
    u.role = 'admin'
    u.save()
    print('Admin user created')
else:
    print('Admin user exists')

# 3. Ensure email is verified for Google OAuth
user = User.objects.filter(email='hyunseo1458@gmail.com').first()
if user:
    EmailAddress.objects.update_or_create(
        user=user, email='hyunseo1458@gmail.com',
        defaults={'verified': True, 'primary': True}
    )

# 4. Setup Google OAuth SocialApp
client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
if client_id:
    site = Site.objects.get_current()
    app, created = SocialApp.objects.get_or_create(
        provider='google',
        defaults={'name': 'Google', 'client_id': client_id, 'secret': os.environ.get('GOOGLE_CLIENT_SECRET', '')}
    )
    app.sites.add(site)
    if created:
        print('Google OAuth configured')
    else:
        print('Google OAuth exists')

print(f'Activities: {Activity.objects.count()}, Categories: {Category.objects.count()}')
"

# 5. Fetch Google Places data if DB is empty
ACTIVITY_COUNT=$(python -c "import django,os;os.environ['DJANGO_SETTINGS_MODULE']='config.settings';django.setup();from activities.models import Activity;print(Activity.objects.count())")
if [ "$ACTIVITY_COUNT" -lt "10" ]; then
    echo "==> Fetching Google Places data..."
    python manage.py fetch_places || echo "==> Fetch failed (check API key)"
fi

echo "==> Starting server..."
exec gunicorn config.wsgi:application
