import json
import secrets
from pathlib import Path
from datetime import date
from difflib import get_close_matches

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.contrib.gis.geos import Point

from users.const import *
from users.models import (
    Profile, User, UserPhoto, generate_unique_username,
    State, LGA
)
from users.countries_states import *

# Define the path to the embedded JSON file
JSON_FILE_PATH = Path(__file__).resolve().parent.parent / "data" / "users.json"


class Command(BaseCommand):
    help = 'Import users and profiles from an embedded Firebase JSON backup and update additional fields'

    def find_choice_key(self, value, choices, default=None):
        """Fuzzy match choice labels and return the key"""
        if not value:
            return default

        clean_value = str(value).strip().lower()
        choice_map = {label.lower(): key for key, label in choices}
        labels = list(choice_map.keys())

        # Try exact match first
        if clean_value in labels:
            return choice_map[clean_value]

        # Try close matches
        matches = get_close_matches(clean_value, labels, n=1, cutoff=0.7)
        if matches:
            return choice_map[matches[0]]

        return default

    def process_location(self, user_data):
        """Process country and state data with intelligent matching"""
        country = self.find_choice_key(
            user_data.get('selected_country') or user_data.get('current_country'),
            COUNTRY_CHOICES
        )

        state = None
        if country == 'NG':  # Nigeria
            state = self.find_choice_key(
                user_data.get('selected_state') or user_data.get('current_state'),
                NIGERIA_STATES
            )

        return {
            'selected_country': country,
            'country': country,
            'selected_state': state,
            'state': state,
            'selected_lga': user_data.get('selected_local_goverment_area', '')
        }

    def process_choices(self, user_data):
        """Process all choice-based fields"""
        return {
            'gender': self.find_choice_key(user_data.get('gender'), GENDER_CHOICES, 'O'),
            'body_type': self.find_choice_key(user_data.get('body_type'), BODY_TYPE_CHOICES, 'AV'),
            'complexion': self.find_choice_key(user_data.get('complexion'), COMPLEXION_CHOICES, 'MD'),
            'smoking': self.find_choice_key(user_data.get('how_often_do_you_smoke'), SMOKING_CHOICES, 'N'),
            'drinking': self.find_choice_key(user_data.get('how_often_do_you_drink'), DRINKING_CHOICES, 'N'),
            'do_you_have_pets': self.find_choice_key(user_data.get('do_you_have_pets'), DO_YOU_HAVE_PETS_CHOICES, 'D'),
            'do_you_have_kids': self.find_choice_key(user_data.get('do_you_have_kids'), DO_YOU_HAVE_KIDS_CHOICES, 'D'),
            'relationship_goal': self.find_choice_key(user_data.get('relationship_goal'), RELATIONSHIP_CHOICES, 'NSR'),
        }

    def import_user(self, data):
        """Process and import a single user"""
        try:
            # Generate temporary password
            temp_password = secrets.token_urlsafe(12)

            # Generate unique username
            display_name = data['name'].strip()[:50]  # Use the name as the display name
            username = generate_unique_username(data['email'], display_name=display_name)

            # Create or update User
            user, created = User.objects.update_or_create(
                email=data['email'],
                defaults={
                    'old_id': data.get('id'),
                    'username': username,
                    'first_name': data['name'].split()[0] if ' ' in data['name'] else data['name'],
                    'last_name': data['name'].split()[-1] if ' ' in data['name'] else '',
                    'email_verified': data.get('email_verified', False),
                    'phone': data.get('phone'),
                    'phone_verified': data.get('phone_verified', False),
                    'device_token': data.get('device_token', '')
                }
            )

            if created:
                user.set_password(temp_password)
                user.save()
                self.stdout.write(f"Created user {user.email} with temp password: {temp_password}")
            else:
                self.stdout.write(f"Updated existing user {user.email}")

            # Process profile data
            profile_data = {
                'display_name': data['name'].strip()[:20],
                'bio': data.get('bio', '')[:500],
                'date_of_birth': self.parse_dob(data),
                **self.process_location(data),
                **self.process_choices(data),
                'latitude': data.get('geo_point', {}).get('geopoint', {}).get('latitude'),
                'longitude': data.get('geo_point', {}).get('geopoint', {}).get('longitude'),
                'address': data.get('current_address', '')[:255],
                'user_status': 'PA',
                'profile_visibility': 'VE'
            }
            Profile.objects.update_or_create(
                user=user,
                defaults=profile_data
            )

            self.process_photos(user, data)
            return True, None  # Indicate success

        except Exception as e:
            return False, str(e)  # Indicate failure with error message

    def parse_dob(self, data):
        try:
            return date(
                year=data.get('birth_year', 1970),
                month=data.get('birth_month', 1),
                day=data.get('birth_day', 1)
            )
        except ValueError:
            return None

    def process_photos(self, user, data):
        # Handle primary photo
        if profile_photo := data.get('profile_photo'):
            UserPhoto.objects.update_or_create(
                user=user,
                image_url=profile_photo,
                defaults={'is_primary': True}
            )
        # Handle additional photos
        for idx, photo_url in enumerate(data.get('photos', [])):
            UserPhoto.objects.update_or_create(
                user=user,
                image_url=photo_url,
                defaults={'order': idx + 1, 'is_primary': False}
            )

    # ---------------------------
    # Additional update functions
    # ---------------------------
    def update_display_names(self):
        """Update profiles with empty or 'Unknown' display names"""
        profiles = Profile.objects.filter(
            Q(display_name__isnull=True) | Q(display_name='') | Q(display_name='Unknown')
        )
        updated_count = 0
        for profile in profiles:
            profile.display_name = profile.user.username[:20]
            profile.save()
            updated_count += 1
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} display names."))

    def update_profile_locations(self):
        """Migrate latitude/longitude data to GIS PointField for profiles missing location data"""
        profiles = Profile.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False,
            location__isnull=True
        )
        updated_count = 0
        for profile in profiles:
            try:
                profile.location = Point(float(profile.longitude), float(profile.latitude))
                profile.save()
                updated_count += 1
            except (TypeError, ValueError) as e:
                self.stdout.write(self.style.WARNING(f"Failed to update profile {profile.id}: {str(e)}"))
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} profile locations."))

    def predict_locations(self):
        """
        Predict and update Nigerian profiles' state and LGA based on temporary fields:
        - Uses 'selected_statee' and 'selected_lgaa' to find the proper State and LGA.
        """
        # Create mapping from state code to state name from NIGERIA_STATES
        state_code_to_name = {code: name for code, name in NIGERIA_STATES}
        profiles = Profile.objects.filter(selected_country="NG")
        updated_count = 0

        for profile in profiles:
            # Assuming these temporary fields exist on your Profile model
            state_code = getattr(profile, 'selected_statee', None)
            lga_input = getattr(profile, 'selected_lgaa', None)

            if state_code:
                state_name = state_code_to_name.get(state_code)
                if state_name:
                    try:
                        state_obj = State.objects.get(name__iexact=state_name)
                        profile.selected_state = state_obj
                        self.stdout.write(self.style.SUCCESS(
                            f"Profile {profile.pk}: Set selected_state to '{state_name}'"
                        ))
                    except State.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"Profile {profile.pk}: State '{state_name}' not found."
                        ))
                        profile.selected_state = None
                else:
                    self.stdout.write(self.style.WARNING(
                        f"Profile {profile.pk}: No mapping found for state code '{state_code}'"
                    ))
                    profile.selected_state = None
            else:
                profile.selected_state = None

            if profile.selected_state and lga_input:
                try:
                    lga_obj = LGA.objects.get(state=profile.selected_state, name__iexact=lga_input)
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

        self.stdout.write(self.style.SUCCESS(f"Successfully updated predicted locations for {updated_count} profiles."))

    # ---------------------------
    # Main handle function
    # ---------------------------
    def handle(self, *args, **kwargs):
        errors = []
        error_profiles = []

        try:
            # Load the embedded JSON file
            with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            success = 0

            for idx, user_data in enumerate(users_data, 1):
                try:
                    result, error = self.import_user(user_data)
                    if result:
                        success += 1
                        if idx % 10 == 0:
                            self.stdout.write(f"Processed {idx} users...")
                    else:
                        errors.append({
                            'index': idx,
                            'data': user_data,
                            'error': error
                        })
                        error_profiles.append(user_data)
                except Exception as e:
                    errors.append({
                        'index': idx,
                        'data': user_data,
                        'error': str(e)
                    })
                    error_profiles.append(user_data)

            if errors:
                error_log_file = JSON_FILE_PATH.parent / "users_errors.json"
                error_profile_log_file = JSON_FILE_PATH.parent / "profile_errors.json"
                with open(error_log_file, 'w', encoding='utf-8') as error_f:
                    json.dump(errors, error_f, indent=4, ensure_ascii=False)
                with open(error_profile_log_file, 'w', encoding='utf-8') as error_ff:
                    json.dump(error_profiles, error_ff, indent=4, ensure_ascii=False)
                self.stdout.write(self.style.WARNING(f"\nError details written to: {error_log_file}"))

            self.stdout.write(self.style.SUCCESS(
                f"\nImport complete!\nSuccessfully processed: {success} users\nErrors: {len(errors)}\n"
            ))

            # Run additional update steps after migration
            self.stdout.write("Running additional updates...")
            self.update_display_names()
            self.update_profile_locations()
            self.predict_locations()
            self.stdout.write(self.style.SUCCESS("All updates complete!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Fatal error: {str(e)}"))
