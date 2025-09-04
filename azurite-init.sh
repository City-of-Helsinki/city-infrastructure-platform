#!/bin/sh

set -e
set -u

# NOTE (2025-09-11 thiago): This is public info
# https://github.com/Azure/Azurite/blob/92743bac3cf580c6dfe1ecc9ac777a6ce16cd985/README.md#connection-strings
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
