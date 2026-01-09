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
    return {
        "TOTAL_VISITORS": cache.get("ga4_total_users", 0)
    }