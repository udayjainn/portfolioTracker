from fastapi import Request
from fastapi.responses import JSONResponse


class NotFoundException(Exception):
    def __init__(self, detail: str = "Resource not found"):
        self.detail = detail


class BadRequestException(Exception):
    def __init__(self, detail: str = "Bad request"):
        self.detail = detail


class UnauthorizedException(Exception):
    def __init__(self, detail: str = "Unauthorized"):
        self.detail = detail


async def not_found_handler(request: Request, exc: NotFoundException):
    return JSONResponse(status_code=404, content={"detail": exc.detail})


async def bad_request_handler(request: Request, exc: BadRequestException):
    return JSONResponse(status_code=400, content={"detail": exc.detail})


async def unauthorized_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(status_code=401, content={"detail": exc.detail})
