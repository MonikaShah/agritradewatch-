from django.core.management.base import BaseCommand
from django.core.cache import cache
from Agritradewatch.utils.ga4 import get_total_users

class Command(BaseCommand):
    help = "Update GA4 total users cache"

    def handle(self, *args, **kwargs):
        users = get_total_users()
        cache.set("ga4_total_users", users, None)
        self.stdout.write(self.style.SUCCESS(f"GA users updated: {users}"))
