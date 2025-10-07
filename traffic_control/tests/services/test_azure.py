import pytest

from traffic_control.services.azure import get_azure_icons_base_url

# Define a single list of test cases for parametrization
AZURITE_CONN_STRING = (
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)

TEST_CASES = [
    # 1. Azurite/Connection String
    (
        "azurite_conn_string",
        {"azure_container": "azurite-icons", "connection_string": AZURITE_CONN_STRING, "overwrite_files": True},
        "http://127.0.0.1:10000/devstoreaccount1/azurite-icons/",
    ),
    # 2. Standard Production Keys
    (
        "prod_keys_standard",
        {
            "account_key": "dummy_key",
            "account_name": "prodstorage",
            "azure_container": "prod-icons",
            "overwrite_files": True,
        },
        "https://prodstorage.blob.core.windows.net/prod-icons/",
    ),
    # 3. Production Keys with Optional 'location' (Sub-path)
    (
        "prod_keys_with_location",
        {"account_name": "prodstorage", "azure_container": "prod-icons", "location": "hi-res-svg/"},
        "https://prodstorage.blob.core.windows.net/prod-icons/hi-res-svg/",
    ),
    # 4. Location without Trailing Slash (Function should fix this)
    (
        "location_without_trailing_slash",
        {"account_name": "storage2", "azure_container": "data", "location": "images"},
        "https://storage2.blob.core.windows.net/data/images/",
    ),
    # 5. Custom Domain/CDN
    (
        "custom_domain_cdn",
        {"account_name": "storage3", "azure_container": "cdn-cache", "custom_domain": "mycdn.azureedge.net"},
        "https://mycdn.azureedge.net/cdn-cache/",
    ),
    # 6. Custom Domain/CDN with Location
    (
        "custom_domain_with_location",
        {
            "account_name": "storage4",
            "azure_container": "cdn-cache",
            "custom_domain": "mycdn.azureedge.net",
            "location": "v2/",
        },
        "https://mycdn.azureedge.net/cdn-cache/v2/",
    ),
    # 7. Incomplete Configuration (Missing account_name/connection_string)
    (
        "incomplete_configuration",
        {"azure_container": "incomplete"},
        "",
    ),
    # 8. Custom Endpoint Suffix (e.g., Azure China)
    (
        "custom_endpoint_suffix",
        {"account_name": "china-storage", "azure_container": "cn-icons", "endpoint_suffix": "core.chinacloudapi.cn"},
        "https://china-storage.blob.core.chinacloudapi.cn/cn-icons/",
    ),
    # 9. Incomplete Configuration (Missing container)
    (
        "missing_container",
        {"account_name": "test"},
        "",
    ),
]


@pytest.mark.parametrize("test_id, input_options, expected_url", TEST_CASES)
def test_base_url_resolution(test_id, input_options, expected_url):
    """
    Tests various configurations (keys, connection string, custom domains, location)
    by passing the options dictionary directly to the utility function.
    """
    # We call the refactored function, passing the test case's options dictionary directly.
    assert get_azure_icons_base_url(input_options) == expected_url
