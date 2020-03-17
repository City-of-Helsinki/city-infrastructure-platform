# ==============================
FROM python:3.8-slim AS base
# ==============================
LABEL vendor="Anders Innovations Oy"
ENV PYTHONUNBUFFERED 1

RUN mkdir /city-infrastructure-platform && \
    groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -ms /bin/bash appuser
WORKDIR /city-infrastructure-platform

COPY requirements.txt /city-infrastructure-platform/
COPY requirements-prod.txt /city-infrastructure-platform/

RUN apt-get update && \
    mkdir -p /usr/share/man/man1/ /usr/share/man/man3/ /usr/share/man/man7/ && \
    apt-get install -y --no-install-recommends libpq-dev build-essential && \
    apt-get install -y --no-install-recommends gdal-bin postgresql-client && \
    pip install --no-cache-dir -r requirements.txt -r requirements-prod.txt && \
    apt-get remove -y build-essential libpq-dev && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/archives

COPY docker-entrypoint.sh /usr/local/bin
ENTRYPOINT ["docker-entrypoint.sh"]

# ==============================
FROM base AS development
# ==============================
COPY requirements-dev.txt /city-infrastructure-platform/
RUN pip install --no-cache-dir -r requirements-dev.txt

ENV DEBUG=1
ENV APPLY_MIGRATIONS=1
ENV COLLECT_STATIC=1
ENV DEV_SERVER=1

COPY . /city-infrastructure-platform
RUN chown -R appuser:appuser /city-infrastructure-platform
USER appuser
EXPOSE 8000

# ==============================
FROM base AS production
# ==============================
ENV APPLY_MIGRATIONS=1
ENV COLLECT_STATIC=1

COPY . /city-infrastructure-platform
RUN chown -R appuser:appuser /city-infrastructure-platform
USER appuser
EXPOSE 8000
