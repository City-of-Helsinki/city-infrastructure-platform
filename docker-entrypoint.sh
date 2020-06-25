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

# Only translate traffic_control module for now
echo "Updating translations..."
cd traffic_control
../manage.py compilemessages -l fi
cd ..

echo "Checking for odd ENTRYPOINT line in arguments"
echo "Arguments are:"
echo $@
echo
if [[ $@ == *"(nop)  ENTRYPOINT" ]]; then
    echo "ENTRYPOINT found in arguments. Emptying arguments."
    set --
else
    echo "No ENTRYPOINT found in arguments, continuing as is"
fi

# Start server
if [[ ! -z "$@" ]]; then
    echo "Running command $@"
    "$@"
elif [[ "$DEV_SERVER" = "1" ]]; then
    echo "Starting dev-server..."
    python ./manage.py runserver 0.0.0.0:8000
else
    echo "Starting uwsgi-server..."
    uwsgi --ini uwsgi_docker.ini
fi
