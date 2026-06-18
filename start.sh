#!/usr/bin/env bash
set -o errexit

echo "==> Running migrations..."
python manage.py migrate --no-input

echo "==> Seeding data..."
python manage.py seed

echo "==> Starting server..."
exec gunicorn config.wsgi:application
