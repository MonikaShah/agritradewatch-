import logging
from Agritradewatch.utils.ga import get_total_users

logger = logging.getLogger(__name__)

def analytics_context(request):
    try:
        visitors = get_total_users()
    except Exception as e:
        logger.error(f"GA fetch failed: {e}")
        visitors = 0

    return {"TOTAL_VISITORS": visitors}

