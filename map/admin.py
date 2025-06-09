from django.contrib import admin

from map.models import FeatureTypeEditMapping, IconDrawingConfig, Layer


@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    list_display = (
        "identifier",
        "name_fi",
        "name_en",
        "name_sv",
        "is_basemap",
        "order",
        "filter_fields",
        "use_traffic_sign_icons",
        "clustered",
    )
    search_fields = ("identifier", "name_fi", "name_en", "name_sv")
    list_filter = ("is_basemap",)


@admin.register(FeatureTypeEditMapping)
class FeatureTypeEditMappingAdmin(admin.ModelAdmin):
    list_display = ("name", "edit_name")


@admin.register(IconDrawingConfig)
class IconDrawingInfoAdmin(admin.ModelAdmin):
    list_display = ("name", "image_type", "png_size", "enabled")
