#!/bin/sh

set -e
set -u

# NOTE (2025-09-11 thiago): This is public info
# https://github.com/Azure/Azurite/blob/92743bac3cf580c6dfe1ecc9ac777a6ce16cd985/README.md#connection-strings
CONN_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://azurite:10000/devstoreaccount1;"

create_storage_container() {
  echo "Creating azurite storage container '${1}'..."
  az storage container create \
    --name "${1}" \
    --connection-string "${CONN_STRING}"
  echo "Azurite storage container '${1}' created."

  echo "Setting azurite storage container '${1} permissions to public read access..."
  az storage container set-permission \
    --name "${1}" \
    --public-access blob \
    --connection-string "${CONN_STRING}"
  echo "Azurite storage container '${1}' configured for public access."
}

create_storage_container "uploads"
create_storage_container "media"
