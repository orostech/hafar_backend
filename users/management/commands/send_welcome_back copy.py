import json
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User
from notification.email_service import EmailService

class Command(BaseCommand):
    help = "Updates last_seen for all users and sends welcome back emails in batches"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size", type=int, default=500, help="Number of emails per batch"
        )
        parser.add_argument(
            "--delay", type=int, default=1, help="Delay between batches in seconds"
        )
        parser.add_argument(
            "--progress-file",
            type=str,
            default="email_progress.json",
            help="Path to progress file",
        )
        parser.add_argument(
            "--resume", action="store_true", help="Resume from previous progress"
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        delay = options["delay"]
        progress_file = options["progress_file"]
        resume = options["resume"]

        # Load or initialize progress data
        try:
            if resume:
                with open(progress_file, "r") as f:
                    progress = json.load(f)
            else:
                progress = {"processed": [], "succeeded": [], "failed": []}
        except FileNotFoundError:
            progress = {"processed": [], "succeeded": [], "failed": []}

        # Exclude already processed users
        us = User.objects.filter(email='mabsademola@gmail.com')
        all_users = us.exclude(id__in=progress["processed"]).order_by("id")
        # all_users = User.objects.exclude(id__in=progress["processed"]).order_by("id")
        total_users = all_users.count()
        self.stdout.write(f"Total users to process: {total_users}")

        email_service = EmailService()

        for i in range(0, total_users, batch_size):
            batch = all_users[i : i + batch_size]
            self.stdout.write(f"Processing batch {i//batch_size + 1}...")

            # Update last_seen and last_login
            user_ids = [user.id for user in batch]
            print('qw me 1')
            # User.objects.filter(id__in=user_ids).update(last_login=timezone.now())
            print('qw me 2')
            for profile in User.profile.related.related_model.objects.filter(user_id__in=user_ids):
                profile.last_seen = timezone.now()
                profile.save(update_fields=["last_seen"])

            # Prepare emails
            emails = []
            for user in batch:
                emails.append({
                    "From": email_service.default_from_email,
                    "To": user.email,
                    "Subject": "Welcome Back to Our Platform! 🎉",
                    "TextBody": f"Hi {user.profile.display_name},\n\nWe're excited to have you back!",
                    "MessageStream": "outbound",
                })

            # Send batch and track results
            try:
                responses = email_service.client.emails.send_batch(emails)
                print('going')
                batch_progress = {"succeeded": [], "failed": []}
                for idx, response in enumerate(responses):
                    if response["ErrorCode"] == 0:
                        batch_progress["succeeded"].append(batch[idx].email)
                    else:
                        batch_progress["failed"].append({
                            "email": batch[idx].email,
                            "error": response["Message"]
                        })
                
                progress["processed"].extend(user_ids)
                progress["succeeded"].extend(batch_progress["succeeded"])
                progress["failed"].extend(batch_progress["failed"])
                self.stdout.write(
                    self.style.SUCCESS(f"Batch {i//batch_size + 1}: {len(batch_progress['succeeded'])} succeeded, {len(batch_progress['failed'])} failed")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
                print(f'going no {e}')
                progress["failed"].extend([{"email": user.email, "error": str(e)} for user in batch])
                progress["processed"].extend(user_ids)

            # Save progress and throttle
            with open(progress_file, "w") as f:
                # Convert UUID objects to strings before saving
                processed = [str(uid) for uid in progress["processed"]]
                progress["processed"] = processed
                json.dump(progress, f, indent=2)
            time.sleep(delay)

        self.stdout.write(self.style.SUCCESS("✅ Completed sending emails!"))