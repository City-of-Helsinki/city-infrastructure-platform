#!/bin/bash

# Utility script for grabbing the icons from the blobstorage and dumping them onto into a local archive.
# Helpful for archiving icons and grabbing an initial set of icons for populating the local database / azurite storage.
#
# Either export AZURE_ACCOUNT_NAME, AZURE_BLOBSTORAGE_CONTAINER_PUBLIC and AZURE_SAS_TOKEN_PUBLIC or run
# source .prepare-azure-scripts.{test,stag,prod}
# before running this script with those definitions before running this script

set -eu

DOWNLOAD_DIR="./download-batch-icons"
mkdir -p "$DOWNLOAD_DIR"

az storage blob download-batch \
    --account-name="$AZURE_ACCOUNT_NAME" \
    --source="$AZURE_BLOBSTORAGE_CONTAINER_PUBLIC" \
    --sas-token="$AZURE_SAS_TOKEN_PUBLIC" \
    --destination="$DOWNLOAD_DIR" \
    --pattern="icons/*"
