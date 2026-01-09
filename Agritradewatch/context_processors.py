# Agritradewatch/context_processors.py
from django.core.cache import cache

# Safe import of GA function
try:
    from .utils.ga4 import get_total_users
except ImportError:
    # fallback if ga4.py is missing
    get_total_users = lambda: 0
    print("GA4 import failed: using dummy get_total_users function")

def analytics_context(request):
    print("DEBUG: analytics_context running")
    """
    Adds GA total users to template context for footer.
    Cached for 5 minutes.
    """
    total = cache.get("total_visitors")
    if total is None:
        try:
            total = get_total_users()
            print("GA total users:", total)  # debug output in console
        except Exception as e:
            print("GA fetch failed:", e)
            total = 0  # fallback if GA API fails
        cache.set("total_visitors", total, 300)  # cache 5 minutes
    print("DEBUG: get_total_users output =", total)
    
    return {"total_visitors": total}
