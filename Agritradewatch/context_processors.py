from django.core.cache import cache

def analytics_context(request):
    total = cache.get("ga4_total_users", 0)
    return {"total_visitors": total}
