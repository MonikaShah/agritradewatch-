from django.core.management.base import BaseCommand
from django.core.cache import cache

from Agritradewatch.utils.ga import get_total_users


class Command(BaseCommand):
    help = "Update Google Analytics total users and cache it"

    def handle(self, *args, **options):
        try:
            users = get_total_users()
            cache.set("TOTAL_VISITORS", users, timeout=60 * 60 * 6)  # 6 hours
            self.stdout.write(self.style.SUCCESS(
                f"GA users updated: {users}"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Failed to update GA users: {e}"
            ))
