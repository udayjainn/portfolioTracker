import math

from app.schemas.common import PaginatedResponse, PaginationMeta


def build_paginated_response(data: list, total: int, page: int, limit: int) -> dict:
    return {
        "data": data,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": math.ceil(total / limit) if limit > 0 else 0,
        },
    }
