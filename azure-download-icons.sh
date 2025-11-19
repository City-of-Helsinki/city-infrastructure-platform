#!/bin/bash

# Utility script for grabbing the icons from the blobstorage and dumping them onto into a local archive.
# Helpful for archiving icons and grabbing an initial set of icons for populating the local database / azurite storage.
#
# Either export AZURE_ACCOUNT_NAME, AZURE_BLOBSTORAGE_CONTAINER_ICONS and AZURE_SAS_TOKEN_ICON or run
# source .prepare-azure-scripts.{test,stag,prod}
# before running this script with those definitions before running this script

set -eu

DOWNLOAD_DIR="./download-batch-icons"
mkdir -p "$DOWNLOAD_DIR"

# PRE-STORAGE-MIGRATION WORKAROUNDS
export AZURE_BLOBSTORAGE_CONTAINER_ICONS="$AZURE_BLOBSTORAGE_CONTAINER_OLD"
export AZURE_SAS_TOKEN_ICON="$AZURE_SAS_TOKEN_OLD"

az storage blob download-batch \
    --dryrun \
    --account-name="$AZURE_ACCOUNT_NAME" \
    --source="$AZURE_BLOBSTORAGE_CONTAINER_ICONS" \
    --sas-token="$AZURE_SAS_TOKEN_ICON" \
    --destination="$DOWNLOAD_DIR" \
    --pattern="icons/*"
