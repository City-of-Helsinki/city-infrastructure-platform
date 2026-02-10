ARG VERSION=""

# ==============================
FROM public.ecr.aws/docker/library/python:3.11-slim-bookworm AS base
# ==============================
LABEL vendor="City of Helsinki"
ENV PYTHONUNBUFFERED 1

RUN mkdir /city-infrastructure-platform && \
    groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -ms /bin/bash appuser
WORKDIR /city-infrastructure-platform

COPY poetry.lock pyproject.toml /city-infrastructure-platform/

RUN apt-get update && \
    mkdir -p /usr/share/man/man1/ /usr/share/man/man3/ /usr/share/man/man7/ && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg && \
    curl -fsSL --proto '=https' --tlsv1.2 https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/postgresql-archive-keyring.gpg] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libcairo2 \
        libpcre3-dev \
        libpq-dev \
        build-essential \
        gdal-bin \
        postgresql-client-17 \
        gettext \
        mime-support && \
    curl -sSL --retry 5 https://install.python-poetry.org --output install-poetry.py && \
    python install-poetry.py --version=1.7.1 && \
    rm install-poetry.py && \
    /root/.local/bin/poetry config virtualenvs.create false && \
    /root/.local/bin/poetry install --only main --no-interaction && \
    pip install --no-cache-dir --upgrade "wheel>=0.46.2" && \
    apt-get remove -y build-essential libpq-dev gnupg && \
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
FROM public.ecr.aws/docker/library/node:20-slim AS build
# ===================================
WORKDIR /map-view
COPY map-view/ .
RUN yarn install --frozen-lockfile --no-cache --production --ignore-scripts --network-timeout 300000 && \
    yarn build

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
