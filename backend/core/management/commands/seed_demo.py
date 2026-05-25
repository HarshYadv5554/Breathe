from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import DataSource, Organization, OrganizationMembership, PlantLookup

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo tenant, analyst user, plant lookups, and data sources"

    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(
            slug="acme-corp",
            defaults={"name": "ACME Corporation (Demo)"},
        )

        user, created = User.objects.get_or_create(
            username="analyst",
            defaults={"email": "analyst@acme.demo", "is_staff": True},
        )
        if created:
            user.set_password("breathe2026")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created analyst / breathe2026"))

        OrganizationMembership.objects.get_or_create(
            user=user, organization=org, defaults={"role": "analyst"}
        )

        plants = [
            ("1000", "Frankfurt Manufacturing", "DE", "Hesse"),
            ("2000", "Chicago Distribution", "US", "IL"),
            ("3000", "Singapore Hub", "SG", "SG"),
        ]
        for code, name, country, region in plants:
            PlantLookup.objects.get_or_create(
                organization=org,
                plant_code=code,
                defaults={"site_name": name, "country": country, "region": region},
            )

        sources = [
            (DataSource.SourceType.SAP_MM, "SAP MM — Fuel & Procurement"),
            (DataSource.SourceType.UTILITY_PORTAL, "Utility Portal — Electricity"),
            (DataSource.SourceType.TRAVEL_CONCUR, "Concur — Business Travel"),
        ]
        for st, label in sources:
            DataSource.objects.get_or_create(
                organization=org, source_type=st, label=label
            )

        self.stdout.write(self.style.SUCCESS(f"Demo org ready: {org.name} (id={org.id})"))
