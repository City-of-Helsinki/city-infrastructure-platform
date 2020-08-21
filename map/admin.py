from django.contrib import admin

from map.models import Layer


@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    list_display = ("identifier", "name_fi", "name_en", "is_basemap", "order")
    search_fields = ("identifier", "name_fi", "name_en")
    list_filter = ("is_basemap",)
