ARG VERSION=""

# ==============================
FROM python:3.8-slim AS base
# ==============================
LABEL vendor="Anders Innovations Oy"
ENV PYTHONUNBUFFERED 1

RUN mkdir /city-infrastructure-platform && \
    groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -ms /bin/bash appuser
WORKDIR /city-infrastructure-platform

COPY poetry.lock pyproject.toml /city-infrastructure-platform/

RUN apt-get update && \
    mkdir -p /usr/share/man/man1/ /usr/share/man/man3/ /usr/share/man/man7/ && \
    apt-get install -y --no-install-recommends \
        libpcre3-dev \
        libpq-dev \
        build-essential \
        gdal-bin \
        postgresql-client \
        git \
        gettext \
        mime-support \
        curl && \
    curl -sSL --retry 5 https://install.python-poetry.org | python - && \
    /root/.local/bin/poetry config virtualenvs.create false && \
    /root/.local/bin/poetry install --no-dev --no-interaction && \
    apt-get remove -y build-essential libpq-dev git && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/archives && \
    rm -rf /root/.cache/pypoetry && \
    rm -rf /root/.cache/pip

COPY docker-entrypoint.sh /usr/local/bin
ENTRYPOINT ["docker-entrypoint.sh"]

# ==============================
FROM base AS development
# ==============================

ENV DEBUG=1
ENV APPLY_MIGRATIONS=1
ENV COLLECT_STATIC=1
ENV DEV_SERVER=1

RUN /root/.local/bin/poetry install
COPY . /city-infrastructure-platform
RUN chown -R appuser:appuser /city-infrastructure-platform
USER appuser
EXPOSE 8000

# ===================================
FROM node:16-slim AS build
# ===================================
COPY map-view/ /map-view/
RUN cd /map-view && \
    yarn install --frozen-lockfile --no-cache --production --network-timeout 300000 && \
    yarn build --network-timeout 300000

# ==============================
FROM base AS production
# ==============================
ARG VERSION

ENV VERSION=${VERSION}
ENV APPLY_MIGRATIONS=0
ENV COLLECT_STATIC=1

COPY . /city-infrastructure-platform
COPY --from=build /map-view/build/ /city-infrastructure-platform/map-view/build/

# OpenShift runs container in arbitrary user which belongs to group `root` (0)
RUN chgrp -R 0 /city-infrastructure-platform && \
    chmod -R g=u /city-infrastructure-platform
USER appuser:0

EXPOSE 8000
