from django.core.management.base import BaseCommand
from users.models import User
from wallet.models import Wallet
class Command(BaseCommand):
    help = 'Create wallet for users who do not have one'

    def handle(self, *args, **kwargs):
        users_without_wallets = User.objects.filter(wallet__isnull=True)
        wallets = [Wallet(user=user) for user in users_without_wallets]

        if wallets:
            Wallet.objects.bulk_create(wallets)
            self.stdout.write(self.style.SUCCESS(f"Successfully created {len(wallets)} wallets"))
        else:
            self.stdout.write(self.style.SUCCESS("All users already have wallets. No action needed."))




