from django.core.cache import cache

def analytics_context(request):
    visitors = cache.get("TOTAL_VISITORS", 0)
    return {
        "TOTAL_VISITORS": visitors
    }
