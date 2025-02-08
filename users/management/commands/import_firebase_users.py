import json
import secrets
import string
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from users.models import Profile, User, UserPhoto, generate_unique_username
from django.utils.timezone import datetime
from datetime import date
# python manage.py import_firebase_users "C:\Users\hp\Documents\Django\hafar backup\firebase_backend_firebase_backup\first_100_users.json"
# py manage.py import_firebase_users "C:\Users\hp\Documents\Django\hafar backup\firebase_backend_firebase_backup\first_100_users.json"


class Command(BaseCommand):
    help = 'Import users and profiles from Firebase JSON backup'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file containing user data')

    def generate_secure_password(self):
        """Generate a secure random password"""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for i in range(16))

    def parse_date_of_birth(self, year, month, day):
        """Parse date of birth from components"""
        try:
            return date(year=year, month=month, day=day)
        except (ValueError, TypeError):
            return None

    def import_single_user(self, data):
        """Import a single user and their profile"""
        temp_password = self.generate_secure_password()
        
        try:
            # Create User with temporary password
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'old_id': data.get('id', ''),
                    'first_name': data['name'].split()[0].strip() if ' ' in data['name'] else data['name'].strip(),
                    'last_name': data['name'].split()[-1].strip() if ' ' in data['name'] else '',
                    'email_verified': data['email_verified'],
                    'phone': data.get('phone', ''),
                    'phone_verified': data['phone_verified'],
                    'device_token': data.get('device_token', '')
                }
            )

            if created:
                user.username = generate_unique_username(user.email, user.first_name)
                user.set_password(temp_password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"User created: {user.email} (temporary password: {temp_password})"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"User already exists: {user.email}")
                )

            # Handle gender conversion
            gender_mapping = {
                'male': 'M',
                'female': 'F',
                'other': 'O'
            }
            profile_gender = gender_mapping.get(data['gender'].strip().lower(), 'O')

            # Parse geo_point data
            geo_point = data.get("geo_point", {})
            geopoint = geo_point.get("geopoint", {})
            latitude = geopoint.get("latitude")
            longitude = geopoint.get("longitude")

            # Parse date of birth
            date_of_birth = self.parse_date_of_birth(
                data.get('birth_year'),
                data.get('birth_month'),
                data.get('birth_day')
            )

            # Create/Update Profile
            profile_data = {
                'user': user,
                'display_name': data['name'].strip(),
                'bio': data.get('bio', ''),
                'date_of_birth': date_of_birth,
                'gender': profile_gender,
                'latitude': latitude,
                'longitude': longitude,
                'address': data.get('current_address', ''),
                'state': data.get('current_state', ''),
                'country': data.get('current_country', ''),
                'selected_address': data.get('current_address', ''),
                'selected_state': data.get('selected_state', ''),
                'selected_country': data.get('selected_country', ''),
                'selected_lga': data.get('selected_local_goverment_area', ''),
                'user_status': 'PA',
                'body_type': 'AV',
                'complexion': 'MD',
                'smoking': 'N',
                'drinking': 'N',
            }

            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults=profile_data
            )

            if not created:
                for key, value in profile_data.items():
                    setattr(profile, key, value)
                profile.save()

            # Handle photos
            if data.get('profile_photo'):
                UserPhoto.objects.get_or_create(
                    user=user,
                    image_url=data['profile_photo'],
                    defaults={'is_primary': True}
                )

            for photo_url in data.get('photos', []):
                UserPhoto.objects.get_or_create(
                    user=user,
                    image_url=photo_url,
                    defaults={'is_primary': False}
                )

            return True, None

        except Exception as e:
            return False, str(e)

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']
        
        try:
            # Load JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            
            # Initialize counters
            total_users = len(users_data)
            successful = 0
            failed = 0
            
            self.stdout.write(f"Starting import of {total_users} users...")
            
            # Process each user
            for idx, user_data in enumerate(users_data, 1):
                success, error = self.import_single_user(user_data)
                
                if success:
                    successful += 1
                else:
                    failed += 1
                    self.stdout.write(
                        self.style.ERROR(f"Failed to import user {user_data.get('email', 'unknown')}: {error}")
                    )
                
                # Progress update
                if idx % 10 == 0:
                    self.stdout.write(f"Processed {idx}/{total_users} users...")
            
            # Final summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nImport completed:\n"
                    f"Total users processed: {total_users}\n"
                    f"Successfully imported: {successful}\n"
                    f"Failed: {failed}"
                )
            )
            
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f"Could not find JSON file: {json_file}")
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR(f"Invalid JSON file: {json_file}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"An error occurred: {str(e)}")
            )