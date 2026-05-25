from django.conf import settings
from django.db import models


class Organization(models.Model):
    """Multi-tenant boundary — every emissions row belongs to one org."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    class Role(models.TextChoices):
        ANALYST = "analyst", "Analyst"
        ADMIN = "admin", "Admin"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ANALYST)

    class Meta:
        unique_together = ("user", "organization")


class PlantLookup(models.Model):
    """SAP Werks/plant codes mean nothing without client-specific mapping."""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    plant_code = models.CharField(max_length=20)
    site_name = models.CharField(max_length=255)
    country = models.CharField(max_length=2, blank=True)
    region = models.CharField(max_length=64, blank=True)

    class Meta:
        unique_together = ("organization", "plant_code")


class DataSource(models.Model):
    """Source-of-truth registry — which system produced data for this tenant."""

    class SourceType(models.TextChoices):
        SAP_MM = "sap_mm", "SAP MM Export (fuel/procurement)"
        UTILITY_PORTAL = "utility_portal", "Utility Portal CSV"
        TRAVEL_CONCUR = "travel_concur", "Corporate Travel Export"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=32, choices=SourceType.choices)
    label = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("organization", "source_type", "label")


class IngestionBatch(models.Model):
    """One upload or API pull — groups raw rows and tracks pipeline status."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    data_source = models.ForeignKey(DataSource, on_delete=models.PROTECT)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    filename = models.CharField(max_length=512, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    row_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    error_summary = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.data_source} — {self.filename or self.pk}"


class RawRecord(models.Model):
    """Immutable-ish capture of source row before normalization."""

    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name="raw_records")
    row_number = models.PositiveIntegerField()
    raw_payload = models.JSONField()
    parse_errors = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["row_number"]


class EmissionActivity(models.Model):
    """
    Normalized activity row — the unit analysts review before audit lock.
    Scope 1/2/3, normalized units, provenance, review state.
    """

    class Scope(models.TextChoices):
        SCOPE_1 = "1", "Scope 1"
        SCOPE_2 = "2", "Scope 2"
        SCOPE_3 = "3", "Scope 3"

    class Category(models.TextChoices):
        STATIONARY_COMBUSTION = "stationary_combustion", "Stationary combustion"
        MOBILE_COMBUSTION = "mobile_combustion", "Mobile combustion"
        PURCHASED_ELECTRICITY = "purchased_electricity", "Purchased electricity"
        PURCHASED_GOODS = "purchased_goods", "Purchased goods"
        BUSINESS_TRAVEL = "business_travel", "Business travel"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        FLAGGED = "flagged", "Flagged — suspicious"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        LOCKED = "locked", "Locked for audit"

    class SuspicionReason(models.TextChoices):
        NONE = "", "None"
        UNIT_MISMATCH = "unit_mismatch", "Unit could not be normalized confidently"
        MISSING_DISTANCE = "missing_distance", "Distance inferred from airport codes"
        BILLING_PERIOD_GAP = "billing_period_gap", "Billing period does not align to calendar month"
        UNKNOWN_PLANT = "unknown_plant", "Plant code not in lookup table"
        HIGH_QUANTITY = "high_quantity", "Quantity exceeds expected range"
        DUPLICATE_SUSPECTED = "duplicate_suspected", "Possible duplicate of existing row"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    batch = models.ForeignKey(IngestionBatch, on_delete=models.PROTECT)
    raw_record = models.OneToOneField(
        RawRecord, on_delete=models.SET_NULL, null=True, blank=True
    )
    data_source = models.ForeignKey(DataSource, on_delete=models.PROTECT)

    scope = models.CharField(max_length=1, choices=Scope.choices)
    category = models.CharField(max_length=40, choices=Category.choices)
    subcategory = models.CharField(max_length=64, blank=True)

    activity_date = models.DateField()
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    site_name = models.CharField(max_length=255, blank=True)
    plant_code = models.CharField(max_length=20, blank=True)
    vendor_or_carrier = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    quantity_raw = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    unit_raw = models.CharField(max_length=32, blank=True)
    quantity_normalized = models.DecimalField(max_digits=18, decimal_places=6)
    unit_normalized = models.CharField(max_length=32)

    source_reference = models.CharField(max_length=128, blank=True)
    source_row_hash = models.CharField(max_length=64, db_index=True)

    review_status = models.CharField(
        max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    suspicion_flags = models.JSONField(default=list, blank=True)
    analyst_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_activities",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    is_edited = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-activity_date", "-created_at"]
        indexes = [
            models.Index(fields=["organization", "review_status"]),
            models.Index(fields=["organization", "scope"]),
        ]


class ActivityAuditLog(models.Model):
    """Append-only audit trail for analyst actions and field edits."""

    class Action(models.TextChoices):
        CREATED = "created", "Created from ingestion"
        EDITED = "edited", "Field edited"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        FLAGGED = "flagged", "Flagged"
        UNFLAGGED = "unflagged", "Unflagged"
        LOCKED = "locked", "Locked for audit"

    activity = models.ForeignKey(
        EmissionActivity, on_delete=models.CASCADE, related_name="audit_logs"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    field_changes = models.JSONField(default=dict, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
