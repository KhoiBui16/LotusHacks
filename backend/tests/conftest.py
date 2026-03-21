"""
Pytest conftest.py — Shared fixtures cho tất cả tests.

Bao gồm:
    - Async HTTP client cho FastAPI endpoint testing
    - Sample incident data fixtures (simple, complex, flood, excluded)
    - Tương thích cả Windows và macOS
"""
import os
import pytest
from unittest.mock import MagicMock, AsyncMock

# Set test environment variables TRƯỚC khi import app
# Để app không fail vì thiếu config khi chạy test
os.environ.setdefault("OPENAI_API_KEY", "test-key-for-unit-tests")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("JWT_SECRET", "test-secret")

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest_asyncio.fixture
async def client():
    """
    Async HTTP client cho testing FastAPI endpoints.

    Dùng ASGITransport để test trực tiếp qua ASGI,
    không cần start server thật.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ══════════════════════════════════════════════════════════════════
# SAMPLE INCIDENT FIXTURES
# ══════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_incident_simple():
    """
    Test data: sự cố ĐƠN GIẢN (trầy xước nhẹ, không bên thứ 3).

    Expected: Triage → SIMPLE, Coverage → ELIGIBLE
    """
    return {
        "time": "2024-06-16 14:00",
        "location": "Quận 1, TP.HCM",
        "gps_coordinates": "10.7769,106.7009",
        "description": "Xe bị trầy xước nhẹ ở cản sau khi đỗ xe",
        "incident_type": "tray_xuoc",
        "third_party_involved": False,
        "vehicle_drivable": True,
        "injuries": False,
        "insurer": "PTI",
        "policy_active": True,
        "policy_start_date": "2024-01-01",
        "policy_end_date": "2024-12-31",
        "driver_license_valid": True,
        "vehicle_registration_valid": True,
        "alcohol_involved": False,
        "highway_incident": False,
        "number_of_vehicles_involved": 1,
        "damage_parts": ["can_sau"],
        "weather_condition": "nắng ráo",
        "road_condition": "bãi đỗ xe bằng phẳng",
    }


@pytest.fixture
def sample_incident_complex():
    """
    Test data: sự cố PHỨC TẠP (tai nạn liên hoàn, thương tích, bên thứ 3).

    Expected: Triage → COMPLEX (rule-based pre-filter, skip LLM)
    """
    return {
        "time": "2024-06-15 08:30",
        "location": "Cao tốc TP.HCM - Long Thành, km 25",
        "gps_coordinates": "10.8231,106.6297",
        "description": "Va chạm liên hoàn 3 xe trên cao tốc do trời mưa trơn.",
        "incident_type": "va_cham",
        "third_party_involved": True,
        "vehicle_drivable": False,
        "injuries": True,
        "insurer": "Bảo Việt",
        "policy_active": True,
        "policy_start_date": "2024-01-01",
        "policy_end_date": "2024-12-31",
        "driver_license_valid": True,
        "vehicle_registration_valid": True,
        "alcohol_involved": False,
        "highway_incident": True,
        "number_of_vehicles_involved": 3,
        "damage_parts": ["can_truoc", "den_pha", "nap_capo"],
        "weather_condition": "mưa lớn",
        "road_condition": "trơn trượt",
        "towing_required": True,
    }


@pytest.fixture
def sample_incident_flood():
    """
    Test data: sự cố ngập nước / thủy kích (đơn giản).

    Expected: Triage → SIMPLE, Coverage → ELIGIBLE
    Lưu ý: vehicle_drivable=False không còn auto đồng nghĩa với COMPLEX.
    """
    return {
        "time": "2024-07-20 07:00",
        "location": "Quận Bình Thạnh, TP.HCM",
        "gps_coordinates": "10.7972,106.7201",
        "description": "Xe bị ngập nước do mưa lớn, động cơ bị thủy kích",
        "incident_type": "ngap_nuoc",
        "third_party_involved": False,
        "vehicle_drivable": False,
        "injuries": False,
        "insurer": "Bảo Việt",
        "policy_active": True,
        "policy_start_date": "2024-01-01",
        "policy_end_date": "2024-12-31",
        "driver_license_valid": True,
        "vehicle_registration_valid": True,
        "alcohol_involved": False,
        "highway_incident": False,
        "number_of_vehicles_involved": 1,
        "damage_parts": ["dong_co"],
        "weather_condition": "mưa lớn",
        "road_condition": "ngập sâu",
        "towing_required": True,
    }


@pytest.fixture
def sample_incident_excluded():
    """
    Test data: sự cố bị LOẠI TRỪ (say rượu + GPLX hết hạn).

    Expected: Triage → SIMPLE (rule pre-filter không trigger cho exclusion fields),
              Coverage → NOT_ELIGIBLE (rule-based exclusion → skip LLM)
    """
    return {
        "time": "2024-09-10 23:00",
        "location": "Đường Phạm Văn Đồng, Gò Vấp, TP.HCM",
        "gps_coordinates": "10.8386,106.6657",
        "description": "Va chạm với dải phân cách khi lái xe ban đêm",
        "incident_type": "va_cham",
        "third_party_involved": False,
        "vehicle_drivable": True,
        "injuries": False,
        "insurer": "PTI",
        "policy_active": True,
        "policy_start_date": "2024-01-01",
        "policy_end_date": "2024-12-31",
        "driver_license_valid": False,
        "vehicle_registration_valid": True,
        "alcohol_involved": True,
        "highway_incident": False,
        "number_of_vehicles_involved": 1,
        "damage_parts": ["can_truoc"],
        "weather_condition": "khô ráo",
        "road_condition": "ban đêm, ánh sáng yếu",
    }
