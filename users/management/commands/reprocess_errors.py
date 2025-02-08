# users/management/commands/reprocess_errors.py

import json
from pathlib import Path
import secrets
from django.core.management.base import BaseCommand
from users.const import *
from users.models import Profile, User, UserPhoto, generate_unique_username
from datetime import date
from difflib import get_close_matches
from users.countries_states import *

# Define the path to the error log file
ERROR_LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "users_errors.json"

class Command(BaseCommand):
    help = 'Reprocess users from the error log'

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
                    'username': username,  # Add the generated username here
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
            geo_point = data.get('geo_point', {})
            # Process profile data
            profile_data = {
                'display_name': data['name'].strip()[:20],
                'bio': data.get('bio', '')[:500],
                'date_of_birth': self.parse_dob(data),
                **self.process_location(data),
                **self.process_choices(data),
                # 'latitude': data.get('geo_point', {}).get('geopoint', {}).get('latitude'),
                # 'longitude': data.get('geo_point', {}).get('geopoint', {}).get('longitude'),
                'latitude': geo_point.get('geopoint', {}).get('latitude') if geo_point else None,
                'longitude': geo_point.get('geopoint', {}).get('longitude') if geo_point else None,
                'address': data.get('current_address', '')[:255],
                'user_status': 'PA',
                'profile_visibility': 'VE'
            }
            # Create or update Profile
            Profile.objects.update_or_create(
                user=user,
                defaults=profile_data
            )
            
            # Process photos
            self.process_photos(user, data)
            
            return True, None
        except Exception as e:
            return False, str(e)

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

    def handle(self, *args, **kwargs):
        errors = []

        try:
            # Load the error log file
            if not ERROR_LOG_PATH.exists():
                self.stdout.write(self.style.ERROR("Error log file not found."))
                return

            with open(ERROR_LOG_PATH, 'r', encoding='utf-8') as f:
                error_log = json.load(f)

            success = 0

            for entry in error_log:
                user_data = entry['data']
                try:
                    result, error = self.import_user(user_data)
                    if result:
                        success += 1
                        self.stdout.write(f"Successfully reprocessed user: {user_data['email']}")
                    else:
                        errors.append({
                            'index': entry['index'],
                            'data': user_data,
                            'error': error
                        })
                except Exception as e:
                    errors.append({
                        'index': entry['index'],
                        'data': user_data,
                        'error': str(e)
                    })

            # Write updated errors to the same file if needed
            if errors:
                with open(ERROR_LOG_PATH, 'w', encoding='utf-8') as error_f:
                    json.dump(errors, error_f, indent=4, ensure_ascii=False)
                self.stdout.write(self.style.WARNING(f"\nUpdated error details written to: {ERROR_LOG_PATH}"))

            self.stdout.write(self.style.SUCCESS(
                f"\nReprocessing complete!\n"
                f"Successfully reprocessed: {success} users\n"
                f"Remaining errors: {len(errors)}\n"
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Fatal error: {str(e)}"))