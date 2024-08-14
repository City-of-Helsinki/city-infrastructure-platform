#!/bin/bash

set -e

function clean()
{
  if test -f schematest.yaml
  then
    echo "cleaning temporary schemafile"
    rm schematest.yaml
  fi
}


if ! python ./manage.py spectacular --color --file schematest.yaml --validate --lang en
then
  echo "schema generation or validation failure"
  clean
  exit 1
fi

if ! diff schematest.yaml traffic_control/static/traffic_control/openapi/openapi.yaml
then
  echo "You need to regenerate openapi schema"
  clean
  exit 1
fi

clean
