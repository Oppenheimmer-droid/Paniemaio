"""
Tests de integración para endpoints críticos de la API.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_health(client):
    """Test del endpoint de salud básico."""
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert "app" in r.json()


@pytest.mark.asyncio
async def test_health_detailed(client):
    """Test del endpoint de salud detallado."""
    r = await client.get("/health/detailed")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "checks" in data
    assert "version" in data
    assert data["checks"]["api"] == "ok"


@pytest.mark.asyncio
async def test_root(client):
    """Test del endpoint raíz."""
    r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Test de login con credenciales inválidas."""
    r = await client.post("/api/v1/auth/login", json={
        "email": "noexiste@test.com",
        "password": "wrong",
        "tenant_slug": "demo"
    })
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    """Test de endpoint protegido sin token."""
    r = await client.get("/api/v1/documents")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_protected_endpoint_invalid_token(client):
    """Test de endpoint protegido con token inválido."""
    r = await client.get(
        "/api/v1/documents",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert r.status_code == 403