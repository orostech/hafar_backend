import json
import secrets
import string
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from users.models import Profile, User, UserPhoto, generate_unique_username
from django.utils.timezone import datetime
from datetime import date

class Command(BaseCommand):
    help = 'Import a single user and profile from JSON data'

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

    def handle(self, *args, **kwargs):
        # The JSON data you provided
        data = {
            "photos": [
                "https://firebasestorage.googleapis.com/v0/b/hafar-b5749.appspot.com/o/profile_images%2F009Gz5AKBteeaYZaY8k6qVc4kFj2%2Fphoto_1?alt=media&token=1098235d-2400-49d9-a6c5-238045798e11"
            ],
            "signup_date": 1734468981140,
            "are_you_a_fit_fam": "sometimes",
            "activity_log": {
                "total_logins": 1,
                "messages_sent": 0,
                "profile_visits": 0,
                "messages_received": 0
            },
            "status": "awaiting_approval",
            "email_verified": True,
            "total_visitors": 1,
            "name": "Usaini Ibrahim",
            "how_many_kids_do_you_have": None,
            "total_likes_received": 9,
            "phone": None,
            "selected_state": "kano",
            "phone_verified": False,
            "profile_photo": "https://firebasestorage.googleapis.com/v0/b/hafar-b5749.appspot.com/o/profile_images%2F009Gz5AKBteeaYZaY8k6qVc4kFj2%2Fprofile_photo?alt=media&token=cd9fa2b4-74c4-4e90-8051-6702e15b646e",
            "bio": "",
            "id": "009Gz5AKBteeaYZaY8k6qVc4kFj2",
            "birth_month": 1,
            "complexion": "brown",
            "how_often_do_you_drink": "i don’t drink",
            "current_local_goverment_area": None,
            "ratings": {},
            "religious_views": None,
            "do_you_have_pets": "i don’t like pets",
            "whoCanMessage": {
                "premium_user": False,
                "anyone": True,
                "liked": False,
                "matched": True
            },
            "preferences": {},
            "weight_kg": None,
            "subscription_plan": None,
            "gender": "male",
            "keep_me_posted": False,
            "age": 29,
            "do_you_have_kids": "no",
            "what_is_your_love_language": "other",
            "current_state": "federal capital territory",
            "height": 48,
            "demo_account": False,
            "body_type": "average",
            "love_to_meet": "Female",
            "privacy_settings": {
                "share_location": False,
                "share_profile_with_search_engines": False,
                "show_online_status": True
            },
            "how_often_do_you_smoke": "i don’t smoke",
            "selected_country": "nigeria",
            "social_links": {},
            "introvert_extrovert": None,
            "id_verified": False,
            "blocked_users": [],
            "total_disliked": 0,
            "selected_local_goverment_area": "dala",
            "marital_status": "divorced",
            "average_rating": 5.0,
            "current_address": "Kano, Kano, Nigeria",
            "birth_day": 1,
            "interest": [],
            "relationship_goal": "short-term fun",
            "birth_year": 1995,
            "device_token": "fU_-HW1zT3iCJnSr_pqw2-:APA91bGvxN4brwCk9w5dESPN6SlSLYr2nqV7O66QVeG_SV-DeFJQ5RXbsrRYhOjph-e-rqnSg2r9PByIy35Gi0FqwlzfUyS9ZomyEHkTywFRDq1lHGPsz4c",
            "geo_point": {
                "geohash": "s4nh3j3vm",
                "geopoint": {
                    "latitude": 12.0268163,
                    "longitude": 8.484075
                }
            },
            "total_matches": 2,
            "email": "usainii646@gmail.com",
            "current_country": "nigeria",
            "last_login": 1734604944524,
            "last_active": 1734604944524
        }


        # Generate a secure random password for the user
        temp_password = self.generate_secure_password()
        print(temp_password)
        
        try:
            # Create User with temporary password
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'old_id': data.get('id', ''),
                    'first_name': data['name'].split()[0] if ' ' in data['name'] else data['name'],
                    'last_name': data['name'].split()[-1] if ' ' in data['name'] else '',
                    'email_verified': data['email_verified'],
                    'phone': data.get('phone', ''),
                    'phone_verified': data['phone_verified'],
                    'device_token': data.get('device_token', '')
                }
            )

            if created:
                user.username = generate_unique_username(user.email, user.first_name)
                # Set the temporary password only for new users
                user.set_password(temp_password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"User created: {user.email} (temporary password generated)"
                    )
                )
                # Here you might want to trigger a password reset email
                # user.send_password_reset_email()  # Implement this method
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
                'display_name': data['name'],
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
                'user_status': 'PA',  # Pending Approval
                'body_type': 'AV',  # Default to Average
                'complexion': 'MD',  # Default to Medium
                'smoking': 'N',  # Default to No
                'drinking': 'N',  # Default to No
            }

            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults=profile_data
            )

            if not created:
                # Update existing profile
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

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported user {user.email}\n'
                    f'Temporary password: {temp_password if created else "[existing user]"}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing user: {str(e)}')
            )