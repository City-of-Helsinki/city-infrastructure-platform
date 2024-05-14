from tablib import import_set

file_formats = (
    "csv",
    "xlsx",
)


def get_import_dataset(resource, format=None, delete_columns=[], queryset=None):
    """
    Utility function for generating Dataset for data import.
    Model resource data is exported to a file format defined in `format`.
    """
    if format not in file_formats:
        raise ValueError(f"Invalid file format {format}. Must be in one of {file_formats}.")

    dataset = resource().export(queryset=queryset)

    for column in delete_columns:
        del dataset[column]

    file_data = getattr(dataset, format)
    return import_set(file_data, format)
