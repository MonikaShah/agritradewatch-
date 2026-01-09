# Agritradewatch/context_processors.py
from django.core.cache import cache

try:
    from .ga4 import get_total_users
except ImportError:
    get_total_users = lambda: 0  # fallback if import fails

def analytics_context(request):
    total = cache.get("total_visitors")
    if total is None:
        try:
            total = get_total_users()
        except Exception as e:
            print("GA fetch failed:", e)
            total = 0
        cache.set("total_visitors", total, 300)
    return {"total_visitors": total}
