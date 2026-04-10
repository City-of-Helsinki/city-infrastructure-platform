ARG VERSION=""

# ==============================
FROM public.ecr.aws/docker/library/python:3.11-slim-bookworm AS base
# ==============================
LABEL vendor="City of Helsinki"
ENV PYTHONUNBUFFERED=1

# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
# https://github.com/astral-sh/uv/pkgs/container/uv/772159347?tag=0.11.3
COPY --from=ghcr.io/astral-sh/uv:0.11.3@sha256:90bbb3c16635e9627f49eec6539f956d70746c409209041800a0280b93152823 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_FROZEN=1
ENV UV_LINK_MODE=copy
ENV UV_NO_CACHE=1
ENV PATH="/city-infrastructure-platform/.venv/bin:$PATH"

RUN mkdir /city-infrastructure-platform && \
    groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -ms /bin/bash appuser
WORKDIR /city-infrastructure-platform

COPY uv.lock pyproject.toml /city-infrastructure-platform/

RUN apt-get update && \
    mkdir -p /usr/share/man/man1/ /usr/share/man/man3/ /usr/share/man/man7/ && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg && \
    curl -fsSL --proto '=https' --tlsv1.2 https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/postgresql-archive-keyring.gpg] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    apt-get update && \
    apt-get install -y --only-upgrade --no-install-recommends openssl libssl3 && \
    apt-get install -y --no-install-recommends \
        libcairo2 \
        libpcre3-dev \
        libpq-dev \
        build-essential \
        gdal-bin \
        postgresql-client-17 \
        gettext \
        mime-support && \
    uv sync --frozen --no-cache --no-dev && \
    uv pip install --no-cache "wheel==0.46.2" && \
    apt-get remove -y build-essential libpq-dev gnupg && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/archives

COPY docker-entrypoint.sh /usr/local/bin
ENTRYPOINT ["docker-entrypoint.sh"]

# ==============================
FROM base AS development
# ==============================

ENV DEBUG=1
ENV COLLECT_STATIC=1
ENV DEV_SERVER=1

RUN uv sync --frozen --no-cache
COPY . /city-infrastructure-platform
USER appuser
EXPOSE 8000

# ===================================
FROM public.ecr.aws/docker/library/node:20-slim AS build
# ===================================
WORKDIR /map-view
COPY map-view/ .
RUN corepack enable
RUN YARN_ENABLE_SCRIPTS=false yarn install --immutable --immutable-cache --check-cache
RUN yarn build

# ==============================
FROM base AS production
# ==============================
ARG VERSION

ENV VERSION=${VERSION}
ENV COLLECT_STATIC=1

COPY . /city-infrastructure-platform
COPY --from=build /map-view/build/ /city-infrastructure-platform/map-view/build/

# We override OIDC_AUTHENTICATION_ENABLED for these commands because we don't have the proper settings for OIDC
# authentication at docker image build time, and this will cause ImproperlyConfigured exceptions to be thrown in
#the pipelines, even though these commands don't care about the settings
RUN OIDC_AUTHENTICATION_ENABLED=0 uv run manage.py collectstatic --noinput && \
    OIDC_AUTHENTICATION_ENABLED=0 ./compilemessages.sh \

# OpenShift runs container in arbitrary user which belongs to group `root` (0)
RUN chgrp -R 0 /city-infrastructure-platform && \
    chmod -R g=u /city-infrastructure-platform
USER appuser:0

EXPOSE 8000
