from django.db.models import NOT_PROVIDED
from django.utils.encoding import force_str
from import_export import fields, widgets


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
            raise KeyError(
                "Key '%s' not found in enum. Available keys are: %s" % (self.column_name, [e.name for e in self.enum])
            )
        data[self.column_name] = enum_value
        return super().clean(data, **kwargs)
