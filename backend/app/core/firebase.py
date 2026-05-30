"""Initialize Firebase Admin once per process (required for verify_id_token)."""

import json
import logging

import firebase_admin
from firebase_admin import credentials

from app.config import settings

logger = logging.getLogger(__name__)


def init_firebase() -> bool:
    """Return True if Firebase Admin is ready to verify tokens."""
    if firebase_admin._apps:
        return True

    if not settings.FIREBASE_CREDENTIALS_JSON:
        if settings.ENVIRONMENT == "production":
            logger.error(
                "FIREBASE_CREDENTIALS_JSON is required in production for auth/watchlist routes"
            )
        else:
            logger.warning(
                "Firebase credentials not configured; auth routes will reject tokens until set"
            )
        return False

    try:
        cred_dict = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin initialized")
        return True
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        logger.exception("Invalid FIREBASE_CREDENTIALS_JSON: %s", exc)
        return False


def ensure_firebase() -> None:
    if not init_firebase():
        from app.core.exceptions import UnauthorizedException

        raise UnauthorizedException("Authentication service is not configured")
