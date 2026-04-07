#!/bin/bash

set -e

uv run manage.py compilemessages -i ".venv/*" -i "map-view/*" -l fi -l sv
