import json
from django.core.management.base import BaseCommand
from users.models import State, LGA
from pathlib import Path

JSON_FILE_PATH = Path(__file__).resolve().parent.parent / "data" / "lgs.json"

class Command(BaseCommand):
    help = "Load states and LGAs from a JSON file"

    def handle(self, *args, **kwargs):
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        for state_data in data:
            state_name = state_data["state"]
            alias = state_data.get("alias", "")
            state_obj, created = State.objects.get_or_create(name=state_name, defaults={"alias": alias})

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created state: {state_name}"))

            for lga_name in state_data.get("lgas", []):
                lga_obj, lga_created = LGA.objects.get_or_create(state=state_obj, name=lga_name)
                if lga_created:
                    self.stdout.write(self.style.SUCCESS(f"  Created LGA: {lga_name}"))

        self.stdout.write(self.style.SUCCESS("Successfully loaded all states and LGAs."))
