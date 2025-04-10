def replace__restore_caches(self, instances) -> bool:
    """
    NOTE: this needs to be removed when corresponding github issue is fixed.
    replace ChunkedQuerySetIterator._restore_caches so it works also with
    fields that do not have .attname. Just ignores cache restore for those fields, eg OneToOneField.
    github issue: https://github.com/Amsterdam/django-gisserver/issues/51
    """
    if not instances:
        return True
    if not self._fk_caches:
        return False

    all_restored = True

    for lookup, cache in self._fk_caches.items():
        field = instances[0]._meta.get_field(lookup)
        for instance in instances:
            id_value = None
            if hasattr(field, "attname"):
                id_value = getattr(instance, field.attname)
            if id_value is None:
                continue

            obj = cache.get(id_value, None)
            if obj is not None:
                instance._state.fields_cache[lookup] = obj
            else:
                all_restored = False

    return all_restored
