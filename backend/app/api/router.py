from fastapi import APIRouter

from app.api.v1 import activity, alerts, auth, compare, investors, notifications, search, securities, watchlists

api_router = APIRouter()

api_router.include_router(investors.router)
api_router.include_router(securities.router)
api_router.include_router(search.router)
api_router.include_router(auth.router)
api_router.include_router(watchlists.router)
api_router.include_router(alerts.router)
api_router.include_router(notifications.router)
api_router.include_router(activity.router)
api_router.include_router(compare.router)
