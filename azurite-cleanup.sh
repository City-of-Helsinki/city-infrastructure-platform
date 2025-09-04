#!/bin/sh

set -e
set -u

# NOTE (2025-09-11 thiago): This is public info
# https://github.com/Azure/Azurite/blob/92743bac3cf580c6dfe1ecc9ac777a6ce16cd985/README.md#connection-strings
readonly CONN_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://azurite:10000/devstoreaccount1;"

echo "Deleting 'media' container..."
az storage container delete \
  --name media \
  --connection-string "${CONN_STRING}"

echo "Azurite 'media' container deleted."
