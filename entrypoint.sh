#!/bin/sh
# Apply database migrations on start, then hand off to the main process (CMD).
set -e

python manage.py migrate --noinput

exec "$@"
