from django.db.models import NOT_PROVIDED
from django.utils.encoding import force_str
from import_export import fields, widgets
from import_export.resources import ModelResource

from users.utils import get_system_user


class EnumIntegerWidget(widgets.Widget):
    def clean(self, value, row=None, *args, **kwargs):
        return value

    def render(self, value, obj=None):
        return force_str(value.name)


class ResourceEnumIntegerField(fields.Field):
    def __init__(
        self,
        attribute=None,
        column_name=None,
        enum=None,
        default=NOT_PROVIDED,
        readonly=False,
        saves_null_values=True,
    ):
        if enum is None:
            raise TypeError
        self.enum = enum
        super().__init__(attribute, column_name, EnumIntegerWidget(), default, readonly, saves_null_values)

    def clean(self, data, **kwargs):
        name = data[self.column_name]
        try:
            enum_value = self.enum.__getattr__(name)
        except AttributeError:
            if name in self.empty_values and self.default != NOT_PROVIDED:
                if callable(self.default):
                    enum_value = self.default()
                else:
                    enum_value = self.default
            else:
                raise KeyError(
                    "Key '%s' not found in enum. Available keys are: %s"
                    % (self.column_name, [e.name for e in self.enum])
                )

        data[self.column_name] = enum_value
        return super().clean(data, **kwargs)


class GenericDeviceBaseResource(ModelResource):
    def get_queryset(self):
        return self._meta.model.objects.active()

    def after_import_instance(self, instance, new, row_number=None, **kwargs):
        """Set created_by and updated_by users"""
        user = kwargs.pop("user", None)
        if user is None:
            user = get_system_user()

        instance.updated_by = user
        if new:
            instance.created_by = user

        super().after_import_instance(instance, new, row_number=None, **kwargs)
