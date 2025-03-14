import json
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User
from notification.email_service import EmailService
from django.utils.html import strip_tags
from pathlib import Path
from django.template.loader import render_to_string

# # Initial run with 0.5s delay between emails
# python manage.py send_welcome_back --throttle 0.5

# # Resume failed attempts
# python manage.py send_welcome_back --resume

# # For morning/afternoon batches (process 2000 users):
# python manage.py send_welcome_back --throttle 0.3 --batch-size 2000

class Command(BaseCommand):
    help = "Sends welcome back emails individually with progress tracking"

    def add_arguments(self, parser):
        parser.add_argument(
            "--throttle", type=float, default=0.5,
            help="Delay between individual emails in seconds"
        )
        parser.add_argument(
            "--resume", action="store_true", help="Resume from previous progress"
        )

    def handle(self, *args, **options):
        throttle = options["throttle"]
        progress_file = Path(__file__).resolve().parent.parent / "data" / "email_progress.json"
        # "email_progress.json"
        resume = options["resume"]

        # Load or create progress data
        try:
            if resume:
                with open(progress_file, "r") as f:
                    progress = json.load(f)
            else:
                progress = {"processed": [], "succeeded": [], "failed": []}
        except FileNotFoundError:
            progress = {"processed": [], "succeeded": [], "failed": []}

        # Get unprocessed users
        # print(progress["processed"])
        # us = User.objects.filter(email='mabspromote@gmail.com')
        all_users = User.objects.exclude(id__in=progress["processed"]).order_by("id")
        total_users = all_users.count()
        self.stdout.write(f"Total users to process: {total_users}")

        email_service = EmailService()
        processed_count = 0

        for user in all_users:
            # print(user.id)
            try:
                # Update user activity
                user.last_login = timezone.now()
                user.save(update_fields=["last_login"])
                user.profile.last_seen = timezone.now()
                user.profile.save(update_fields=["last_seen"])

                context = {
                    'user': user,
                    'site_name': 'Hafar',
                    'play_store_url': "https://play.google.com/store/apps/details?id=com.orostech.hafar"
                }

                html_content = render_to_string(
                    f'emails/platform_back_announcement.html', context)
                text_content = strip_tags(html_content)
                subject = "Welcome Back to Our Platform! 🎉"

                # Prepare and send email
                response = email_service.client.emails.send(
                    From=email_service.default_from_email,
                    To=user.email,
                    Subject=subject,
                    HtmlBody=html_content,
                    TextBody=text_content,
                    MessageStream="outbound"
                )

                if response["ErrorCode"] == 0:
                    progress["succeeded"].append(user.email)
                    self.stdout.write(f"✅ Success: {user.email}")
                else:
                    progress["failed"].append({
                        "email": user.email,
                        "error": response["Message"]
                    })
                    self.stdout.write(f"❌ Failed: {user.email} - {response['Message']}")

            except Exception as e:
                error_msg = str(e)
                progress["failed"].append({
                    "email": user.email,
                    "error": error_msg
                })
                self.stdout.write(f"🚨 Error: {user.email} - {error_msg}")

            finally:
                # Update progress after each user
                progress["processed"].append(str(user.id))
                processed_count += 1

                # Save progress every 50 users
                if processed_count % 50 == 0:
                    with open(progress_file, "w") as f:
                        json.dump(progress, f, indent=2)
                    self.stdout.write(f"💾 Saved progress after {processed_count} users")

                # Throttle requests
                time.sleep(throttle)

        # Final progress save
        with open(progress_file, "w") as f:
            json.dump(progress, f, indent=2)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Completed! Success: {len(progress['succeeded'])}, Failed: {len(progress['failed'])}"
        ))