from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from users.models import Profile

class Command(BaseCommand):
    help = 'Migrate latitude/longitude data to GIS PointField'

    def handle(self, *args, **options):
        # Get profiles with valid coordinates but no GIS point
        profiles = Profile.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            location__isnull=True
        )

        updated_count = 0

        for profile in profiles:
            try:
                # Create Point object (longitude first per GIS convention)
                profile.location = Point(float(profile.longitude), float(profile.latitude))
                profile.save()
                updated_count += 1
            except (TypeError, ValueError) as e:
                self.stdout.write(self.style.WARNING(
                    f"Failed to update profile {profile.id}: {str(e)}"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Successfully updated {updated_count}/{len(profiles)} profiles"
        ))