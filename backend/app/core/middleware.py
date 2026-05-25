from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
)

RATE_LIMITS = {
    "anonymous": "60/minute",
    "authenticated": "300/minute",
    "search": "30/minute",
    "premium": "1000/minute",
}
