# ==============================
FROM python:3.8-slim AS base
# ==============================
ENV PYTHONUNBUFFERED 1

# Create a place for the code
RUN mkdir /city-infrastructure-platform
WORKDIR /city-infrastructure-platform

COPY requirements.txt /city-infrastructure-platform/
COPY requirements-prod.txt /city-infrastructure-platform/

RUN apt-get update && \
    #
    # -slim packages does not include man directories
    # and they are needed by postgresql-client
    #
    mkdir -p /usr/share/man/man1/ /usr/share/man/man3/ /usr/share/man/man7/ && \
    #
    # Build dependencies
    #
    apt-get install -y --no-install-recommends libpq-dev build-essential && \
    #
    # Run dependencies
    #
    apt-get install -y --no-install-recommends gdal-bin postgresql-client && \
    pip install --no-cache-dir -r requirements.txt -r requirements-prod.txt && \
    #
    # Cleanup
    #
    apt-get remove -y build-essential libpq-dev && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/archives

COPY docker-entrypoint.sh /city-infrastructure-platform
ENTRYPOINT ["./docker-entrypoint.sh"]

# ==============================
FROM base AS development
# ==============================
COPY requirements-dev.txt /city-infrastructure-platform/
RUN pip install --no-cache-dir -r requirements-dev.txt

# Set up start command
ENV APPLY_MIGRATIONS=1
ENV DEV_SERVER=1
ENTRYPOINT ["./docker-entrypoint.sh"]

# ==============================
FROM base AS production
# ==============================
# Copy code to image
COPY . /city-infrastructure-platform

# Expose application port
EXPOSE 8000/tcp

# Set up start command
COPY uwsgi_docker.ini /city-infrastructure-platform
ENTRYPOINT ["./docker-entrypoint.sh"]
