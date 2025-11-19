#!/bin/bash

# Utility script for grabbing the upload files from the blobstorage and dumping them onto a local archive.
# Helpful for archiving files and grabbing an initial set of icons for populating the local database / azurite storage.
#
# Either export AZURE_ACCOUNT_NAME, AZURE_BLOBSTORAGE_CONTAINER_UPLOADS and AZURE_SAS_TOKEN_UPLOADS or run
# source .prepare-azure-scripts.{test,stag,prod}
# before running this script with those definitions before running this script

set -eu

DOWNLOAD_DIR="./download-batch-planfiles"
mkdir -p "$DOWNLOAD_DIR"

# PRE-STORAGE-MIGRATION WORKAROUNDS
export AZURE_BLOBSTORAGE_CONTAINER_UPLOADS="$AZURE_BLOBSTORAGE_CONTAINER_OLD"
export AZURE_SAS_TOKEN_UPLOADS="$AZURE_SAS_TOKEN_OLD"


az storage blob download-batch \
    --dryrun \
    --account-name="$AZURE_ACCOUNT_NAME" \
    --source="$AZURE_BLOBSTORAGE_CONTAINER_UPLOADS" \
    --sas-token="$AZURE_SAS_TOKEN_UPLOADS" \
    --destination="$DOWNLOAD_DIR" \
    --pattern="planfiles/*"

DOWNLOAD_DIR="./download-batch-realfiles"
mkdir -p "$DOWNLOAD_DIR"

az storage blob download-batch \
    --dryrun \
    --account-name="$AZURE_ACCOUNT_NAME" \
    --source="$AZURE_BLOBSTORAGE_CONTAINER_UPLOADS" \
    --sas-token="$AZURE_SAS_TOKEN_UPLOADS" \
    --destination="$DOWNLOAD_DIR" \
    --pattern="realfiles/*"

