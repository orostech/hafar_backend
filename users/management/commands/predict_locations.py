import json
from django.core.management.base import BaseCommand
from users.models import Profile, State, LGA, NIGERIA_STATES

class Command(BaseCommand):
    help = (
        "Predicts and updates Profile's selected_state and selected_lga "
        "based on the values in selected_statee and selected_lgaa for Nigerian profiles."
    )

    def handle(self, *args, **options):
        # Convert the Nigeria states choices (tuple list) into a dictionary:
        # e.g., {'AD': 'Adamawa', 'AK': 'Akwa Ibom', ...}
        state_code_to_name = {code: name for code, name in NIGERIA_STATES}

        # Filter profiles where the selected_country is Nigeria ('NG')
        profiles = Profile.objects.filter(selected_country="NG")
        updated_count = 0

        for profile in profiles:
            # Get the state code and LGA string from the profile
            state_code = profile.selected_statee
            lga_input = profile.selected_lgaa

            # Process state conversion
            if state_code:
                state_name = state_code_to_name.get(state_code)
                if state_name:
                    try:
                        # Attempt to find the matching State (case-insensitive match)
                        state_obj = State.objects.get(name__iexact=state_name)
                        profile.selected_state = state_obj
                        self.stdout.write(self.style.SUCCESS(
                            f"Profile {profile.pk}: Set selected_state to '{state_name}'"
                        ))
                    except State.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"Profile {profile.pk}: State '{state_name}' not found in the database."
                        ))
                        profile.selected_state = None
                else:
                    self.stdout.write(self.style.WARNING(
                        f"Profile {profile.pk}: No mapping found for state code '{state_code}'"
                    ))
                    profile.selected_state = None
            else:
                profile.selected_state = None

            # Process LGA conversion if a state was successfully matched and LGA input exists
            if profile.selected_state and lga_input:
                try:
                    lga_obj = LGA.objects.get(
                        state=profile.selected_state, name__iexact=lga_input
                    )
                    profile.selected_lga = lga_obj
                    self.stdout.write(self.style.SUCCESS(
                        f"Profile {profile.pk}: Set selected_lga to '{lga_input}'"
                    ))
                except LGA.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"Profile {profile.pk}: LGA '{lga_input}' not found for state '{profile.selected_state.name}'."
                    ))
                    profile.selected_lga = None
            else:
                profile.selected_lga = None

            profile.save()
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully updated {updated_count} profiles."
        ))
