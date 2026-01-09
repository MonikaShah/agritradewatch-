import logging
from Agritradewatch.utils.ga4 import get_total_users
from django.core.cache import cache

logger = logging.getLogger(__name__)

# def analytics_context(request):
#     visitors = get_total_users() 
#     # try:
#     #     visitors = get_total_users()
#     # except Exception as e:
#     #     logger.error(f"GA fetch failed: {e}")
#     #     visitors = 0

#     return {"TOTAL_VISITORS": visitors}

def analytics_context(request):
    visitors = cache.get("ga4_total_users")

    if visitors is None:
        try:
            visitors = get_total_users()
            cache.set("ga4_total_users", visitors, 60 * 60)  # 1 hour cache
        except Exception as e:
            print("GA4 ERROR:", e)
            visitors = 0

    return {"TOTAL_VISITORS": visitors}
