# ==============================
FROM python:3.8-slim AS base
# ==============================
LABEL vendor="Anders Innovations Oy"
ENV PYTHONUNBUFFERED 1

RUN mkdir /city-infrastructure-platform && \
    mkdir /map-view && \
    groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -ms /bin/bash appuser
WORKDIR /city-infrastructure-platform


RUN apt-get update && \
    mkdir -p /usr/share/man/man1/ /usr/share/man/man3/ /usr/share/man/man7/ && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        build-essential \
        gdal-bin \
        postgresql-client \
        git \
        gettext \
        mime-support \
        curl \
        nodejs \
        npm && \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

ENV PATH = "${PATH}:/root/.poetry/bin"
COPY poetry.lock pyproject.toml /city-infrastructure-platform/

RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction && \
    apt-get remove -y build-essential libpq-dev && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/archives && \
    rm -rf /root/.cache/pip && \
    npm install -g yarn && \
    npm cache clean --force

COPY docker-entrypoint.sh /usr/local/bin
ENTRYPOINT ["docker-entrypoint.sh"]

# ==============================
FROM base AS development
# ==============================

ENV DEBUG=1
ENV APPLY_MIGRATIONS=1
ENV COLLECT_STATIC=1
ENV DEV_SERVER=1

RUN poetry install
COPY . /city-infrastructure-platform
RUN chown -R appuser:appuser /city-infrastructure-platform
USER appuser
EXPOSE 8000

# ===================================
FROM base AS build
# ===================================
COPY map-view/ /map-view/
RUN cd /map-view && \
    yarn install --frozen-lockfile --no-cache --production && \
    yarn build

# ==============================
FROM base AS production
# ==============================
ENV APPLY_MIGRATIONS=1
ENV COLLECT_STATIC=1

COPY . /city-infrastructure-platform
COPY --from=build /map-view/build/ /city-infrastructure-platform/map-view/build/
RUN chown -R appuser:appuser /city-infrastructure-platform
USER appuser
EXPOSE 8000
