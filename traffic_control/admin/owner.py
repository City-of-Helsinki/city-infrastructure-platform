from django.contrib import admin

from ..models import Owner


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = [
        "name_fi",
        "name_en",
        "id",
    ]
    ordering = ("name_fi",)
