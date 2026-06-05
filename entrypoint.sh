#!/bin/sh
# Apply database migrations on start, then hand off to the main process (CMD).
set -e

# Ensure the media directory exists (e.g. the Railway volume mount point).
# Non-fatal: if it already exists or is not writable, keep going.
[ -n "$MEDIA_ROOT" ] && mkdir -p "$MEDIA_ROOT" 2>/dev/null || true

python manage.py migrate --noinput

exec "$@"
