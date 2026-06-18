#!/usr/bin/env bash

echo "==> Running migrations..."
python manage.py migrate --no-input

echo "==> Seeding data..."
python manage.py seed || echo "==> Seed skipped (may already exist)"

echo "==> Starting server..."
exec gunicorn config.wsgi:application
