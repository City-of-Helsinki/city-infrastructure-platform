from urllib.parse import urljoin

def get_azure_storage_base_url(options: dict) -> str:
    """
    Retrieves the base path/URL for an azure storage backend
    :param options: The 'OPTIONS' dictionary from the Django STORAGES setting.
    :return: The calculated base URL string.
    """
    container = options.get("azure_container")
    if not container:
        # Configuration is too incomplete
        return ""

    # 1. Check for connection_string (Azurite/Local Dev)
    if "connection_string" in options:
        conn_string = options["connection_string"]

        # Connection string contains the full BlobEndpoint
        # Safely parse the connection string parts
        parts = {}
        for part in conn_string.split(";"):
            if "=" in part:
                key, value = part.split("=", 1)
                parts[key] = value

        if "BlobEndpoint" in parts:
            endpoint = parts["BlobEndpoint"]
            # Reconstruct: BlobEndpoint + Container Name
            # Use rstrip('/') for cleanliness before joining
            base_url = urljoin(f"{endpoint.rstrip('/')}/", f"{container}/")
            return base_url

    # 2. Fallback to individual keys (Production/Standard Azure)
    elif "account_name" in options:
        account_name = options["account_name"]

        # Check for custom domain (CDN)
        custom_domain = options.get("custom_domain")

        if custom_domain:
            # If using a custom domain, use it directly as the host
            hostname = custom_domain.rstrip("/")
            base_url = f"https://{hostname}/"
        else:
            # Standard Azure Blob URL format
            endpoint_suffix = options.get("endpoint_suffix", "core.windows.net")
            hostname = f"{account_name}.blob.{endpoint_suffix}"
            base_url = f"https://{hostname}/"

        # Standard Azure format: https://[host]/[container]/[location]
        # Append container name to the host URL
        full_base_url = urljoin(base_url, f"{container}/")

        # Append location if used
        location = options.get("location", "")
        if location:
            # Append location to the existing base URL (which already contains the container)
            return urljoin(full_base_url, f"{location.rstrip('/')}/")

        return full_base_url

    # Fallback if configuration is incomplete (e.g., missing account_name)
    return ""
