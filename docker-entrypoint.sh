#!/bin/bash

set -e

# Apply database migrations
if [[ "$APPLY_MIGRATIONS" = "1" ]]; then
    echo "Applying database migrations..."
    python ./manage.py migrate --noinput
fi

# Collect static files
if [[ "$COLLECT_STATIC" = "1" ]]; then
    echo "Collecting static files..."
    ./manage.py collectstatic --noinput
fi

echo "Updating translations..."
./manage.py compilemessages -l fi

# Start server
if [[ ! -z "$@" ]]; then
    "$@"
elif [[ "$DEV_SERVER" = "1" ]]; then
    python ./manage.py runserver 0.0.0.0:8000
else
    uwsgi --ini uwsgi_docker.ini
fi
