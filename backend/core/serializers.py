from django.contrib.auth import get_user_model
from rest_framework import serializers

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

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ("id", "source_type", "label", "is_active", "created_at")


class PlantLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantLookup
        fields = ("id", "plant_code", "site_name", "country", "region")


class IngestionBatchSerializer(serializers.ModelSerializer):
    data_source_label = serializers.CharField(source="data_source.label", read_only=True)
    source_type = serializers.CharField(source="data_source.source_type", read_only=True)

    class Meta:
        model = IngestionBatch
        fields = (
            "id",
            "data_source",
            "data_source_label",
            "source_type",
            "filename",
            "status",
            "row_count",
            "success_count",
            "error_count",
            "warning_count",
            "error_summary",
            "started_at",
            "completed_at",
        )


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = ("id", "row_number", "raw_payload", "parse_errors")


class ActivityAuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True, default="")

    class Meta:
        model = ActivityAuditLog
        fields = ("id", "action", "field_changes", "note", "user_name", "created_at")


class EmissionActivitySerializer(serializers.ModelSerializer):
    data_source_type = serializers.CharField(source="data_source.source_type", read_only=True)
    batch_filename = serializers.CharField(source="batch.filename", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.username", read_only=True, default="")
    audit_logs = ActivityAuditLogSerializer(many=True, read_only=True)

    class Meta:
        model = EmissionActivity
        fields = (
            "id",
            "scope",
            "category",
            "subcategory",
            "activity_date",
            "period_start",
            "period_end",
            "site_name",
            "plant_code",
            "vendor_or_carrier",
            "description",
            "quantity_raw",
            "unit_raw",
            "quantity_normalized",
            "unit_normalized",
            "source_reference",
            "source_row_hash",
            "review_status",
            "suspicion_flags",
            "analyst_notes",
            "reviewed_by_name",
            "reviewed_at",
            "is_edited",
            "locked_at",
            "data_source_type",
            "batch_filename",
            "created_at",
            "updated_at",
            "audit_logs",
        )
        read_only_fields = (
            "source_row_hash",
            "is_edited",
            "locked_at",
            "created_at",
            "updated_at",
            "audit_logs",
        )


class EmissionActivityUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionActivity
        fields = (
            "quantity_normalized",
            "unit_normalized",
            "description",
            "analyst_notes",
            "site_name",
        )


class DashboardStatsSerializer(serializers.Serializer):
    total_activities = serializers.IntegerField()
    pending_review = serializers.IntegerField()
    flagged = serializers.IntegerField()
    approved = serializers.IntegerField()
    locked = serializers.IntegerField()
    failed_batches = serializers.IntegerField()
    recent_batches = IngestionBatchSerializer(many=True)
