from django.db.models import CharField, Func


class SplitPart(Func):
    function = "SPLIT_PART"
    arity = 3
    output_field = CharField()
