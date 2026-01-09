# Agritradewatch/context_processors.py
from django.core.cache import cache
from Agritradewatch.utils.ga4 import get_total_users

def analytics_context(request):
    """
    Adds GA total users to template context for footer.
    Cached for 5 minutes.
    """
    total = cache.get("total_visitors")
    if total is None:
        try:
            total = get_total_users()
        except Exception as e:
            print("GA fetch failed:", e)
            total = 0
        cache.set("total_visitors", total, 300)  # cache 5 minutes
    return {"total_visitors": total}
