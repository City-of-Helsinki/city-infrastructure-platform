#!/bin/bash

# Utility script for migrating data from the old unified storage container into the two separate storage containers.
#
# Export the following environment variables before running the script:
#
# AZURE_ACCOUNT_NAME
# AZURE_BLOBSTORAGE_CONTAINER_ICONS
# AZURE_BLOBSTORAGE_CONTAINER_UPLOADS
# AZURE_BLOBSTORAGE_CONTAINER_OLD
# AZURE_SAS_TOKEN_ICON
# AZURE_SAS_TOKEN_UPLOADS
# AZURE_SAS_TOKEN_OLD
#
# or source the appropriate .prepare-azure-scripts.test, .prepare-azure-scripts.stag or .prepare-azure-scripts.prod file
# source .prepare-azure-scripts.{test,stag,prod}

set -eu

transfer_storage_contents() {
  FOLDER_PATH="${1}"
  AZURE_BLOBSTORAGE_CONTAINER_DESTINATION="${2}"
  AZURE_SAS_TOKEN_DESTINATION="${3}"
  az storage blob copy start-batch \
      --dryrun \
      --source-account-name "$AZURE_ACCOUNT_NAME" \
      --source-container "$AZURE_BLOBSTORAGE_CONTAINER_OLD" \
      --pattern "$FOLDER_PATH/*" \
      --source-sas "$AZURE_SAS_TOKEN_OLD" \
      --account-name "$AZURE_ACCOUNT_NAME" \
      --destination-container "$AZURE_BLOBSTORAGE_CONTAINER_DESTINATION" \
      --sas-token "$AZURE_SAS_TOKEN_DESTINATION"
}

transfer_storage_contents "icons" "$AZURE_BLOBSTORAGE_CONTAINER_ICONS" "$AZURE_SAS_TOKEN_ICON"
transfer_storage_contents "planfiles" "$AZURE_BLOBSTORAGE_CONTAINER_UPLOADS" "$AZURE_SAS_TOKEN_UPLOADS"
transfer_storage_contents "realfiles" "$AZURE_BLOBSTORAGE_CONTAINER_UPLOADS" "$AZURE_SAS_TOKEN_UPLOADS"
