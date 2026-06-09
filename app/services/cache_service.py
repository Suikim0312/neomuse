"""High-level caching helpers built on top of the Redis cache client."""
from app.core.cache import cache

POPULAR_EXHIBITS_KEY = "neomuse:exhibits:popular"
DASHBOARD_STATS_KEY = "neomuse:dashboard:stats"

POPULAR_EXHIBITS_TTL = 120
DASHBOARD_TTL = 60


def invalidate_exhibits() -> None:
    cache.delete(POPULAR_EXHIBITS_KEY)


def invalidate_dashboard() -> None:
    cache.delete(DASHBOARD_STATS_KEY)
