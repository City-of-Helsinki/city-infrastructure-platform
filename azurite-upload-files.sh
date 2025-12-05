#!/bin/bash

# Utility script for a dump of file uploads from a deployment and uploading it to your local azurite instance.
# Helpful for setting up your development environment

set -eu

# NOTE (2025-11-19 thiago): This is public info
# https://github.com/Azure/Azurite/blob/92743bac3cf580c6dfe1ecc9ac777a6ce16cd985/README.md#connection-strings
CONN_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
DOWNLOAD_DIR="./download-batch-planfiles"

az storage blob upload-batch \
    --connection-string="$CONN_STRING" \
    --source="$DOWNLOAD_DIR" \
    --destination="uploads" \
    --pattern="*"

DOWNLOAD_DIR="./download-batch-realfiles"

az storage blob upload-batch \
    --connection-string="$CONN_STRING" \
    --source="$DOWNLOAD_DIR" \
    --destination="uploads" \
    --pattern="*"

