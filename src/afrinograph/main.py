from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from afrinograph.logging import setup_logging
from afrinograph.shared.domain.errors import (
    AdapterError,
    AfrinographError,
    ApplicationError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)


def create_app() -> FastAPI:
    """FastAPI application factory."""
    setup_logging()

    app = FastAPI(
        title="Afrinograph - Africa Signal Collector",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ValidationError)
    @app.exception_handler(DomainError)
    async def validation_or_domain_handler(
        request: Request, exc: DomainError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(AdapterError)
    @app.exception_handler(ApplicationError)
    async def application_error_handler(
        request: Request, exc: ApplicationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )

    @app.exception_handler(AfrinographError)
    async def general_afrinograph_handler(
        request: Request, exc: AfrinographError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return app
