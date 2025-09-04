#!/bin/sh

set -e
set -u

CONN_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://azurite:10000/devstoreaccount1;"

echo "Creating 'media' container..."
az storage container create \
  --fail-on-exist \
  --name media \
  --connection-string "${CONN_STRING}"

echo "Setting 'media' container permissions to public read access..."
az storage container set-permission \
  --name media \
  --public-access blob \
  --connection-string "${CONN_STRING}"

echo "Azurite 'media' container created and configured."
