#!/bin/bash

# Utility script for grabbing the upload files from the blobstorage and dumping them onto a local archive.
# Helpful for archiving files and grabbing an initial set of icons for populating the local database / azurite storage.
#
# Either export AZURE_ACCOUNT_NAME, AZURE_BLOBSTORAGE_CONTAINER_PRIVATE and AZURE_SAS_TOKEN_PRIVATE or run
# source .prepare-azure-scripts.{test,stag,prod}
# before running this script with those definitions before running this script

set -eu

DOWNLOAD_DIR="./download-batch-planfiles"
mkdir -p "$DOWNLOAD_DIR"

az storage blob download-batch \
    --account-name="$AZURE_ACCOUNT_NAME" \
    --source="$AZURE_BLOBSTORAGE_CONTAINER_PRIVATE" \
    --sas-token="$AZURE_SAS_TOKEN_PRIVATE" \
    --destination="$DOWNLOAD_DIR" \
    --pattern="planfiles/*"

DOWNLOAD_DIR="./download-batch-realfiles"
mkdir -p "$DOWNLOAD_DIR"

az storage blob download-batch \
    --account-name="$AZURE_ACCOUNT_NAME" \
    --source="$AZURE_BLOBSTORAGE_CONTAINER_PRIVATE" \
    --sas-token="$AZURE_SAS_TOKEN_PRIVATE" \
    --destination="$DOWNLOAD_DIR" \
    --pattern="realfiles/*"

