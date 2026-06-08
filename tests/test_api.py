"""
Comprehensive test suite for PaddyCare AI API.
Run with: pytest tests/ -v
"""
from __future__ import annotations

import io
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app

# ── Test Database Setup ───────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test_paddycare.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables and seed data for tests."""
    Base.metadata.create_all(bind=engine)
    from app.db.init_db import seed_diseases, seed_shops
    db = TestingSessionLocal()
    seed_diseases(db)
    seed_shops(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_token(client: TestClient) -> str:
    """Get a valid auth token using OTP bypass."""
    # Send OTP
    resp = client.post("/api/v1/auth/send-otp", json={"phone": "+919876543210"})
    assert resp.status_code == 200

    # Verify OTP (bypass code)
    resp = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone": "+919876543210", "otp": "123456", "name": "Test Farmer"},
    )
    assert resp.status_code == 200
    return resp.json()["data"]["access_token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}


# ── Health Check ──────────────────────────────────────────────
class TestHealth:
    def test_health_endpoint(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "db_connected" in data

    def test_root_endpoint(self, client: TestClient):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "docs" in resp.json()


# ── Authentication ────────────────────────────────────────────
class TestAuth:
    def test_send_otp_valid_phone(self, client: TestClient):
        resp = client.post("/api/v1/auth/send-otp", json={"phone": "+919000000001"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_send_otp_invalid_phone(self, client: TestClient):
        resp = client.post("/api/v1/auth/send-otp", json={"phone": "123"})
        assert resp.status_code == 422

    def test_verify_otp_wrong_code(self, client: TestClient):
        client.post("/api/v1/auth/send-otp", json={"phone": "+919000000002"})
        resp = client.post(
            "/api/v1/auth/verify-otp",
            json={"phone": "+919000000002", "otp": "000000"},
        )
        assert resp.status_code == 400

    def test_verify_otp_success(self, client: TestClient, auth_token: str):
        assert len(auth_token) > 10

    def test_refresh_token(self, client: TestClient):
        # First get tokens
        client.post("/api/v1/auth/send-otp", json={"phone": "+919000000003"})
        resp = client.post(
            "/api/v1/auth/verify-otp",
            json={"phone": "+919000000003", "otp": "123456"},
        )
        refresh_token = resp.json()["data"]["refresh_token"]

        # Now refresh
        resp2 = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp2.status_code == 200
        assert "access_token" in resp2.json()["data"]


# ── User Profile ──────────────────────────────────────────────
class TestUsers:
    def test_get_profile(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/users/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["phone"] == "+919876543210"
        assert data["name"] == "Test Farmer"

    def test_update_profile(self, client: TestClient, auth_headers: dict):
        resp = client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"name": "Updated Farmer", "language": "ta", "dark_mode": True},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "Updated Farmer"
        assert data["language"] == "ta"

    def test_update_profile_invalid_language(self, client: TestClient, auth_headers: dict):
        resp = client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"language": "fr"},
        )
        assert resp.status_code == 422

    def test_get_profile_unauthorized(self, client: TestClient):
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 403  # or 401


# ── Disease Catalogue ─────────────────────────────────────────
class TestDiseases:
    def test_list_diseases(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/diseases", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 10
        assert len(data["diseases"]) == 10

    def test_get_disease_by_id(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/diseases/1", headers=auth_headers)
        assert resp.status_code == 200
        d = resp.json()["data"]
        assert d["id"] == 1
        assert "recommendations" in d

    def test_get_disease_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/diseases/9999", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_disease_by_class(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/diseases/by-class/0", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Blast Disease"


# ── Shops ─────────────────────────────────────────────────────
class TestShops:
    def test_list_shops(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/shops", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()["data"]) > 0

    def test_nearby_shops(self, client: TestClient, auth_headers: dict):
        resp = client.post(
            "/api/v1/shops/nearby",
            headers=auth_headers,
            json={"latitude": 11.1085, "longitude": 77.3411, "radius_km": 50},
        )
        assert resp.status_code == 200

    def test_get_shop_by_id(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/shops/1", headers=auth_headers)
        assert resp.status_code == 200


# ── History ───────────────────────────────────────────────────
class TestHistory:
    def test_get_empty_history(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/history", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "predictions" in data
        assert "total" in data


# ── Prediction (Scan) ─────────────────────────────────────────
class TestPredictions:
    def test_scan_without_model(self, client: TestClient, auth_headers: dict):
        """Model may not be loaded in tests — expect 503 or 201."""
        # Create a minimal valid JPEG in memory
        img_bytes = io.BytesIO()
        try:
            from PIL import Image as PILImage
            img = PILImage.new("RGB", (224, 224), color=(100, 150, 50))
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)
        except ImportError:
            pytest.skip("Pillow not installed — skipping image test.")

        resp = client.post(
            "/api/v1/predictions/scan",
            headers=auth_headers,
            files={"file": ("leaf.jpg", img_bytes, "image/jpeg")},
        )
        # Accept either success or model-not-loaded
        assert resp.status_code in (201, 503)

    def test_prediction_not_found(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/v1/predictions/99999", headers=auth_headers)
        assert resp.status_code == 404