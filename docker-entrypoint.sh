#!/bin/bash

set -e

echo "Version: $VERSION"

# Apply or validate database migrations
if [[ "$APPLY_MIGRATIONS" = "1" ]]; then
    echo "Applying database migrations..."
    ./apply-migrations.sh
else
    echo "Checking that migrations are applied..."
    error_code=0
    ./check-migrations.sh || error_code=$?

    if [ "$error_code" -ne 0 ]; then
        echo "Migrations are not applied!"
        exit $error_code
    fi
fi

# Collect static files
if [[ "$COLLECT_STATIC" = "1" ]]; then
    echo "Collecting static files..."
    ./manage.py collectstatic --noinput
fi

# Translate messages
echo "Updating translations..."
./manage.py compilemessages -l fi

echo "Checking for odd ENTRYPOINT line in arguments"
echo "Arguments are:"
echo $@
echo
if [[ $@ == *"(nop)  ENTRYPOINT"* ]]; then
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
    UWSGI_ARGS="--ini uwsgi/docker.ini"

    if [[ "$UWSGI_LOG_HEALTHZ" = "1" ]]
    then
        echo "Logging health and readiness check requests."
    else
        echo "Suppressing health and readiness checks requests."
        UWSGI_ARGS="$UWSGI_ARGS --ini uwsgi/donotlog-health.ini"
    fi

    echo "Starting uwsgi-server at $(date)"
    uwsgi $UWSGI_ARGS
fi
