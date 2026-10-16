import httpx
import pytest
from fastapi import FastAPI

from afrinograph.main import create_app
from afrinograph.shared.domain.errors import (
    AdapterError,
    AfrinographError,
    ApplicationError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)


@pytest.fixture
def app() -> FastAPI:
    application = create_app()

    # Add test-only routes for testing exception handlers
    @application.get("/raise-not-found")
    def raise_not_found() -> None:
        raise NotFoundError("Resource missing")

    @application.get("/raise-conflict")
    def raise_conflict() -> None:
        raise ConflictError("Resource conflict")

    @application.get("/raise-validation")
    def raise_validation() -> None:
        raise ValidationError("Invalid input")

    @application.get("/raise-domain")
    def raise_domain() -> None:
        raise DomainError("Domain rule violated")

    @application.get("/raise-application")
    def raise_application() -> None:
        raise ApplicationError("Application fault")

    @application.get("/raise-adapter")
    def raise_adapter() -> None:
        raise AdapterError("Adapter failure")

    @application.get("/raise-internal")
    def raise_internal() -> None:
        raise AfrinographError("Internal fault")

    return application


@pytest.mark.api
@pytest.mark.asyncio
async def test_app_boots(app: FastAPI) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/non-existent-route")
        assert response.status_code == 404


@pytest.mark.api
@pytest.mark.asyncio
async def test_exception_handlers(app: FastAPI) -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        r1 = await client.get("/raise-not-found")
        assert r1.status_code == 404
        assert r1.json() == {"detail": "Resource missing"}

        r2 = await client.get("/raise-conflict")
        assert r2.status_code == 409
        assert r2.json() == {"detail": "Resource conflict"}

        r3 = await client.get("/raise-validation")
        assert r3.status_code == 400
        assert r3.json() == {"detail": "Invalid input"}

        r4 = await client.get("/raise-domain")
        assert r4.status_code == 400
        assert r4.json() == {"detail": "Domain rule violated"}

        r5 = await client.get("/raise-application")
        assert r5.status_code == 500
        assert r5.json() == {"detail": "Application fault"}

        r6 = await client.get("/raise-adapter")
        assert r6.status_code == 500
        assert r6.json() == {"detail": "Adapter failure"}

        r7 = await client.get("/raise-internal")
        assert r7.status_code == 500
        assert r7.json() == {"detail": "Internal server error"}
