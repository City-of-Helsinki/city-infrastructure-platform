from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    value = dictionary.get(key)
    # Nicer formatting for None and empty string values
    if value is None or value == "":
        value = "-"
    return value


@register.filter
def has_key(dictionary, key):
    return key in dictionary
