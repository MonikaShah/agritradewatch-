from django.core.management.base import BaseCommand
from Agritradewatch.utils.ga import get_total_users


class Command(BaseCommand):
    help = "Fetch total GA4 users"

    def handle(self, *args, **kwargs):
        try:
            users = get_total_users()
            self.stdout.write(self.style.SUCCESS(f"GA total users: {users}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(str(e)))
