[![Build status](https://api.travis-ci.com/City-of-Helsinki/city-infrastructure-platform.svg?branch=master)](https://travis-ci.com/github/City-of-Helsinki/city-infrastructure-platform)
[![Codecov](https://codecov.io/gh/City-of-Helsinki/city-infrastructure-platform/branch/master/graph/badge.svg)](https://codecov.io/gh/City-of-Helsinki/city-infrastructure-platform)
[![Requirements](https://requires.io/github/City-of-Helsinki/city-infrastructure-platform/requirements.svg?branch=master)](https://requires.io/github/City-of-Helsinki/city-infrastructure-platform/requirements/?branch=master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# City Infrastructure Platform

City Infrastructure Platform REST-API backend application.

## Development

### Install required system packages

#### PostgreSQL and PostGIS

Install PostgreSQL and PostGIS.

    # Ubuntu 18.04
    sudo apt-get install python3-dev libpq-dev postgresql postgis

#### GeoDjango extra packages

    # Ubuntu 18.04
    sudo apt-get install binutils libproj-dev gdal-bin
    export CPLUS_INCLUDE_PATH=/usr/include/gdal
    export C_INCLUDE_PATH=/usr/include/gdal

### Creating a Python virtualenv

Create a Python 3.x virtualenv either using the [`venv`](https://docs.python.org/3/library/venv.html) tool or using
the great [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) toolset. Assuming the latter,
once installed, simply do:

    mkvirtualenv -p /usr/bin/python3 city-infrastructure-platform

The virtualenv will automatically activate. To activate it in the future, just do:

    workon city-infrastructure-platform

### Creating and updating requirements

* Run `prequ update`

### Installing Python requirements

* Run `pip install -r requirements.txt`
* For development also run `pip install -r requirements-dev.txt`

### Prepare the database

Enable PostGIS extension for the default template

    sudo -u postgres psql -d template1 -c "CREATE EXTENSION IF NOT EXISTS postgis;"

Create user and database

    sudo -u postgres createuser -P -R -S city-infrastructure-platform  # use password `city-infrastructure-platform`
    sudo -u postgres createdb -O city-infrastructure-platform city-infrastructure-platform

Allow user to create test database

    sudo -u postgres psql -c "ALTER USER city-infrastructure-platform CREATEDB;"

### Django configuration

Environment variables are used to customize configuration in `city-infrastructure-platform/settings.py`. If you wish to override any
settings, you can place them in a local `.env` file which will automatically be sourced when Django imports
the settings file.

Copy .env.example file as .env: `cp .env.example .env`

### Running development environment

* Enable debug `echo 'DEBUG=True' >> .env`
* Run `python manage.py migrate`
* Run `python manage.py runserver 0.0.0.0:8000`

### Docker

Build Docker image: `docker build -t city-infrastructure-platform .`

Run container: `docker run -d -p 8000:8000 -e DEBUG=1 city-infrastructure-platform`

**Available configs (environment variables):**

To set any of the settings below, use the `-e <ENV_VAR>=<VALUE>` flag when running the Docker container.

* DATABASE_HOST: Set to the host address of the PostgreSQL (with PostGIS) database server, default is empty value.
* DATABASE_PORT: Set to port of the database server, default is 5432.
* DEV_SERVER: Set to `1` to run `manage.py runserver` instead of `uwsgi`, default is empty value.
* COLLECT_STATIC: Set to `1` to collect static files on startup, default is empty value.
* APPLY_MIGRATIONS: Set to `1` to run `manage.py migrate` on startup, default is empty value.

### Docker Compose

Run the application `docker-compose up`

### Translations (fi)

Run script `./makemessages.sh`
