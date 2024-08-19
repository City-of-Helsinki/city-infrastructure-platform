#!/bin/bash

set -e

python manage.py compilemessages -i "venv/*" -i "map-view/*" -l fi -l sv
