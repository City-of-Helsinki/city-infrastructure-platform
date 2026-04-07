#!/bin/bash

set -e

uv run manage.py spectacular --color --file traffic_control/static/traffic_control/openapi/openapi.yaml --validate --lang en
