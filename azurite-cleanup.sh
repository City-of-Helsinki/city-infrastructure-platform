#!/bin/sh

set -e
set -u

readonly CONN_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://azurite:10000/devstoreaccount1;"

echo "Deleting 'media' container..."
az storage container delete \
  --name media \
  --connection-string "${CONN_STRING}"

echo "Azurite 'media' container deleted."
