#!/bin/sh

set -e
set -u

# NOTE (2025-09-11 thiago): This is public info
# https://github.com/Azure/Azurite/blob/92743bac3cf580c6dfe1ecc9ac777a6ce16cd985/README.md#connection-strings
readonly CONN_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://azurite:10000/devstoreaccount1;"

delete_storage_container() {
  echo "Deleting azurite storage container '${1}'..."
  az storage container delete \
    --name "${1}" \
    --connection-string "${CONN_STRING}"
  echo "Azurite storage container '${1}' deleted."
}

delete_storage_container "uploads"
delete_storage_container "media"
