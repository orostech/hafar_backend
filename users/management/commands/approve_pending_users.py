# app_name/management/commands/approve_pending_users.py
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from ...models import Profile  # Update import according to your app structure

class Command(BaseCommand):
    help = 'Approves pending users who meet profile criteria'

    def handle(self, *args, **options):
        # Fetch pending Nigerian profiles with state selected
        target_profiles = Profile.objects.filter(
            is_verified='PENDING',
            # selected_country='NG',
            # selected_state__isnull=False
        ).select_related('user').prefetch_related('user__photos')

        approved = 0
        for profile in target_profiles:
            # Check if profile has at least one photo
            has_photo = profile.user.photos.exists()
            
            # Check completeness score
            if has_photo and profile.completeness_score >= 0.6:
                profile.is_verified = 'ACTIVE'
                profile.save()
                approved += 1
                self.stdout.write(f'Approved {profile.user.email}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully approved {approved} users.')
        )