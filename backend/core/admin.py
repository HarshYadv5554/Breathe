from django.contrib import admin

from .models import (
    ActivityAuditLog,
    DataSource,
    EmissionActivity,
    IngestionBatch,
    Organization,
    OrganizationMembership,
    PlantLookup,
    RawRecord,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")


@admin.register(EmissionActivity)
class EmissionActivityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "organization",
        "scope",
        "category",
        "activity_date",
        "quantity_normalized",
        "unit_normalized",
        "review_status",
    )
    list_filter = ("review_status", "scope", "category")


admin.site.register(OrganizationMembership)
admin.site.register(PlantLookup)
admin.site.register(DataSource)
admin.site.register(IngestionBatch)
admin.site.register(RawRecord)
admin.site.register(ActivityAuditLog)
