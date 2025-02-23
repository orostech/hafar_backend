from django.core.management.base import BaseCommand
from users.models import User, Profile
from django.db.models import Q


class Command(BaseCommand):
    help = 'Update display names for existing profiles'

    def handle(self, *args, **options):
        # Get profiles with empty, unknown, or null display names
        profiles = Profile.objects.filter(
            Q(display_name__isnull=True) | 
            Q(display_name='') | 
            Q(display_name='Unknown')
        )
        
        updated_count = 0
        for profile in profiles:
            profile.display_name = profile.user.username
            profile.save()
            updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully updated {updated_count} profiles'
        ))