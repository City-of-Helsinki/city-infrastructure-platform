from urllib.parse import urlparse

from storages.backends.azure_storage import AzureStorage


class NonLeakyAzureStorage(AzureStorage):
    def url(self, name, expire=None, parameters=None):
        """
        Return an absolute URL where the file's contents can be accessed directly by a web browser, unless a SAS key is
        required for the access. If a SAS key is present in the storage configuration, this method will omit it.
        """
        result = super().url(name, expire, parameters)
        parsed = urlparse(result)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def url_private(self, name, expire=None, parameters=None):
        """
        Return an absolute URL where the file's contents can be accessed directly by a web browser. If a SAS key is
        present in the storage configuration, this method will expose it to the user code.
        """
        return super().url(name, expire, parameters)
