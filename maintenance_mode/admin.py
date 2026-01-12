from django.contrib import admin

from maintenance_mode.models import MaintenanceMode


@admin.register(MaintenanceMode)
class MaintenanceModeAdmin(admin.ModelAdmin):
    fields = ("is_active", "message_fi", "message_en", "message_sv", "updated_at", "updated_by")
    readonly_fields = ("updated_at", "updated_by")

    def has_add_permission(self, request):
        # Only allow adding if no instance exists
        return not MaintenanceMode.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Never allow deletion
        return False

    def save_model(self, request, obj, form, change):
        # Automatically set updated_by to current user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None):
        # Redirect to edit form if instance exists
        if MaintenanceMode.objects.exists():
            obj = MaintenanceMode.objects.first()
            from django.shortcuts import redirect
            from django.urls import reverse

            return redirect(reverse("admin:maintenance_mode_maintenancemode_change", args=[obj.pk]))
        return super().changelist_view(request, extra_context)
