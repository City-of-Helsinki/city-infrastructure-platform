ARG VERSION=""

# ==============================
FROM helsinki.azurecr.io/ubi9/python-312-gdal AS appbase
# ==============================
LABEL vendor="City of Helsinki"
ENV PYTHONUNBUFFERED=1

# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
# https://github.com/astral-sh/uv/pkgs/container/uv/1086831070?tag=0.12.1 (2026-07-31)
COPY --from=ghcr.io/astral-sh/uv:0.12.1@sha256:cf4eedcaa81655197f625739489effcbe71b61ceb1506f332c3facae5deceded /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_FROZEN=1
ENV UV_LINK_MODE=copy
ENV UV_NO_CACHE=1
ENV PATH="/city-infrastructure-platform/.venv/bin:/usr/pgsql-17/bin:$PATH"
ENV IPYTHONDIR="/city-infrastructure-platform/var/ipython"

# The base image auto-activates its own s2i virtualenv in every bash shell,
# which would shadow the project virtualenv in PATH.
ENV BASH_ENV=""
ENV ENV=""
ENV PROMPT_COMMAND=""

RUN mkdir /city-infrastructure-platform && \
    groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -ms /bin/bash appuser
WORKDIR /city-infrastructure-platform

COPY uv.lock pyproject.toml /city-infrastructure-platform/

# The base image already provides GDAL, GEOS, PROJ, cairo, pcre, libpq-devel,
# gcc/make, python3.12-devel, gettext and mailcap. Only the PostgreSQL 17
# client is missing and is installed from the PGDG repository.
RUN dnf install -y --setopt=install_weak_deps=False \
        https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm && \
    dnf install -y --setopt=install_weak_deps=False postgresql17 && \
    # Keep the PGDG libpq out of the global loader path so that GDAL and
    # psycopg2 keep using the system libpq. psql finds its own via RUNPATH.
    rm -f /etc/ld.so.conf.d/postgresql-pgdg-libs.conf && \
    ldconfig && \
    dnf clean all && \
    rm -rf /var/cache/dnf

RUN uv sync --frozen --no-cache --no-dev && \
    uv pip install --no-cache "wheel==0.46.2"

COPY docker-entrypoint.sh /usr/local/bin
ENTRYPOINT ["docker-entrypoint.sh"]

# ==============================
FROM appbase AS development
# ==============================

ENV DEBUG=1
ENV COLLECT_STATIC=1
ENV DEV_SERVER=1

RUN uv sync --frozen --no-cache
COPY . /city-infrastructure-platform
RUN mkdir -p /city-infrastructure-platform/var/ipython && \
    chown -R appuser:appuser /city-infrastructure-platform/var
USER appuser
EXPOSE 8000

# ===================================
FROM public.ecr.aws/docker/library/node:24-slim AS build
# ===================================
WORKDIR /map-view
COPY map-view/ .
RUN corepack enable
RUN YARN_ENABLE_SCRIPTS=false yarn install --immutable --immutable-cache --check-cache
RUN yarn build

# ==============================
FROM appbase AS production
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
    OIDC_AUTHENTICATION_ENABLED=0 ./scripts/compilemessages.sh \

# OpenShift runs container in arbitrary user which belongs to group `root` (0)
# Create IPython directory for shell_plus and ensure proper permissions
RUN mkdir -p /city-infrastructure-platform/var/ipython && \
    chgrp -R 0 /city-infrastructure-platform && \
    chmod -R g=u /city-infrastructure-platform
USER appuser:0

EXPOSE 8000
