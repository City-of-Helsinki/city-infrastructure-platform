from django.contrib import admin

from traffic_control.models import Owner


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = [
        "name_fi",
        "name_en",
        "id",
    ]
    ordering = ("name_fi",)
