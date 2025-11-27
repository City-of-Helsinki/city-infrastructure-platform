[![Build status](https://api.travis-ci.com/City-of-Helsinki/city-infrastructure-platform.svg?branch=master)](https://travis-ci.com/github/City-of-Helsinki/city-infrastructure-platform)
[![Codecov](https://codecov.io/gh/City-of-Helsinki/city-infrastructure-platform/branch/master/graph/badge.svg)](https://codecov.io/gh/City-of-Helsinki/city-infrastructure-platform)
[![Requirements](https://requires.io/github/City-of-Helsinki/city-infrastructure-platform/requirements.svg?branch=master)](https://requires.io/github/City-of-Helsinki/city-infrastructure-platform/requirements/?branch=master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# City Infrastructure Platform

City Infrastructure Platform REST-API backend application.

## Setting up the environment for development

There are multiple ways to prepare the project for development. Described here is a method to run the auxiliary services using docker containers and a method to run these services directly using system packages. For both paths you should go through the common dependencies and setting up the python environment first.

### Cloning the repository

```bash
git clone git@github.com:City-of-Helsinki/city-infrastructure-platform.git
```

### Setup git hooks

```bash
cd city-infrastructure-platform
./setup-git-hooks.sh
```

### Common dependencies

Install required system packages, some of these are needed to build some of the python project dependencies and some of these are used in runtime.


```bash
sudo apt install binutils gdal-bin libpq-dev libproj-dev pipx
```

Install [Poetry](https://github.com/python-poetry/poetry#installation) for managing python dependencies.

```bash
# Let pipx handle it (without messing with the project's environment, the x at the end of pipx is important!)
pipx install poetry

# Or use the system package (may be less bleeding-edge but good enough for this project)
sudo apt install python3-poetry
```

#### Common dependencies - python environment

Check whether you have the minimum required version of python (3.11.9)

```bash
python --version
```

or

```
python3 --version
```

##### Common dependencies - python environment - use correct python version (optional)

If your version of python is equal to or newer than 3.11.9, you may skip this section.

If your python version is older, we recommend you install [pyenv](https://github.com/pyenv/pyenv) to manage the installation of a newer version, follow the instructions to set up the [suggested build environment](https://github.com/pyenv/pyenv/wiki#suggested-build-environment) for your system, and then finally install and activate python 3.11.9.


```bash
# This command will build python version 3.11.9, it is a lengthy process
# so make sure you have followed the steps for setting up the suggested
# build environment linked above.
pyenv install 3.11.9
```

If you encounter trouble building python 3.11.9 even after setting up the suggested build environment, you should consult the [pyenv common problems FAQ](https://github.com/pyenv/pyenv/wiki/Common-build-problems) to proceed.

```bash
# This command will activate python 3.11.9
pyenv global 3.11.9
```

##### Common dependencies - python environment - virtual environment

Ensure you are using python 3.11.9 or newer and at the root of this project run


```bash
# Create the environment
python -m venv venv

# Activate the environment
source venv/bin/activate

# Install project dependencies (development)
poetry install --no-root

# Install project dependencies (production)
poetry install --no-dev
```

(optional) You can also use poetry to update the project's python dependencies:

```bash
# Update python dependencies / lock file
poetry update
```

### Development environment with docker

Install [docker](https://docs.docker.com/engine/install/ubuntu/), their provided packages are preferred since system packages are likely to be lagging behind the official distribution.

```bash
# Add docker's official repository as described in the link above
# ...
# Install required docker packages
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

#### Development environment with docker - rootless mode (optional)

By default, docker needs to be executed with root privileges, which may put your system at risk of malicious docker images, so you may consider setting [rootless mode](https://docs.docker.com/engine/security/rootless/). If you installed docker using the official packages and the commands suggested in the [install instructions](https://docs.docker.com/engine/install/ubuntu/) on a fresh Ubuntu system it will be as easy as running the following command as a regular user:

```bash
dockerd-rootless-setuptool.sh install
```

The script will be available in your PATH, and will let you know if you are missing any other system packages and give you a command to install them. Follow those steps and re-run the script, and it's done.

### Development environment without docker

**Note:** These instructions are currently outdated, and could use updating to a newer LTS version of Ubuntu

#### Development environment without docker - PostgreSQL and PostGIS

Install PostgreSQL and PostGIS.

```bash
# Ubuntu 18.04
sudo apt-get install python3-dev libpq-dev postgresql postgis
```

#### Development environment without docker - GeoDjango extra packages

```bash
# Ubuntu 18.04
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
```

#### Development environment without docker - Prepare the database

Enable PostGIS extension for the default template

```bash
sudo -u postgres psql -h localhost -d template1 -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

Create user and database

```bash
sudo -u postgres createuser -h localhost -P -R -S city-infrastructure-platform  # use password `city-infrastructure-platform`
sudo -u postgres createdb -h localhost -O city-infrastructure-platform city-infrastructure-platform
```

Allow user to create test database

```bash
sudo -u postgres psql -h localhost -c "ALTER USER city-infrastructure-platform CREATEDB;"
```

## Running the project

### Running the project - Django

Environment variables are used to customize configuration in `cityinfra/settings.py`. If you wish to override any
settings, you can place them in a local `.env` file which will automatically be sourced when Django imports
the settings file.
Another way, easiest with Azurite emulation is to copy cityinfra/local_settings_example.py to cityinfra/local_settings.py and modify the settings there.
Example already sets AZURE_BLOBSTORAGE settings to use Azurite emulation.

```
# Use example configuration
cp .env.example .env


# Enable debug (optional)
echo 'DEBUG=True' >> .env

# Run database migrations
# (Requires that the database is up and running)
python manage.py migrate

# Run server (host defaults to 127.0.0.1 and port defaults to 8000)
# (Requires that the database is up and running)
python manage.py runserver
# or with the local_settings
python manage.py runserver --settings=cityinfra.local_settings
```

#### Running the project - Docker services (without compose)

Build Docker image:

```bash
docker build -t city-infrastructure-platform .
```

Run container:

```bash
docker run -d -p 8000:8000 -e DEBUG=1 city-infrastructure-platform
```

**Available configs (environment variables):**

To set any of the settings below, use the `-e <ENV_VAR>=<VALUE>` flag when running the Docker container.

* DATABASE_HOST: Set to the host address of the PostgreSQL (with PostGIS) database server, default is empty value.
* DATABASE_PORT: Set to port of the database server, default is 5432.
* DEV_SERVER: Set to `1` to run `manage.py runserver` instead of `uwsgi`, default is empty value.
* COLLECT_STATIC: Set to `1` to collect static files on startup, default is empty value.
* APPLY_MIGRATIONS: Set to `1` to run `manage.py migrate` on startup, default is empty value.

#### Running the project - Docker services (with compose)

The file `docker-compose.yml` contains the environment configuration for the different services that can be executed.

Run the entire application, with all its auxiliary services

```bash
docker-compose up
```

##### Running the project - Docker services - individual services

```bash
# Run just the DB
docker-compose up db

# Run ClamAV locally (initialize clamd and then launch clamv-api)
docker compose up clamd
docker compose up clamv-api

# Run azurite (local emulation of azure storage)
# NOTE: To you use azurite you must also set the EMULATE_AZURE_BLOBSTORAGE variable on your .env file to True
docker compose -f docker-compose.azurite.yml up azurite

# Create the media, upload storage containers in azurite and grant it public read permissions for serving static files
docker compose -f docker-compose.azurite.yml up azurite-init

# Wipe the media, upload storage containers on azurite (you will need to re-run azurite-init after this)
docker compose -f docker-compose.azurite.yml up azurite-delete-storage-containers
```

## Translations (fi)

```
# Ensure gettext is installed
sudo apt install gettext

# Run the script
./makemessages.sh
```

## Traffic sign icons

Traffic sign icons are from Finnish Transport Infrastructure Agency which has released these icons in public
domain under Creative Commons 1.0 universal (CC0 1.0) license. Original icons can be found
[here](https://github.com/finnishtransportagency/liikennemerkit/tree/master/collections/new_signs/svg).
