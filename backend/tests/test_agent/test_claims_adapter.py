from datetime import datetime, timezone

from app.models.claim import ClaimInDB
from app.models.vehicle import VehicleInDB
from app.routers.claims import _build_agent_incident_input


def _build_claim(*, description: str, location_text: str, has_third_party: bool) -> ClaimInDB:
    return ClaimInDB.model_validate(
        {
            "_id": "507f1f77bcf86cd799439011",
            "user_id": "507f1f77bcf86cd799439012",
            "vehicle_id": "507f1f77bcf86cd799439013",
            "insurer": "PTI",
            "policy_id": "POL-001",
            "status": "draft",
            "incident": {
                "type": "collision",
                "date": "2026-03-20",
                "time": "20:15",
                "location_text": location_text,
                "description": description,
                "has_third_party": has_third_party,
                "third_party_info": "Xe 30A-99999",
                "can_drive": False,
                "needs_towing": True,
                "has_injury": False,
            },
            "timeline": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "submitted_at": None,
        }
    )


def _build_vehicle() -> VehicleInDB:
    return VehicleInDB.model_validate(
        {
            "_id": "507f1f77bcf86cd799439013",
            "user_id": "507f1f77bcf86cd799439012",
            "plate": "51K-12345",
            "model": "Toyota Vios",
            "year": 2024,
            "color": "white",
            "vehicle_type": "car",
            "policy_linked": True,
            "policy_id": "POL-001",
            "insurer": "PTI",
            "effective_date": "2026-01-01",
            "expiry": "2026-12-31",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
    )


def test_build_agent_incident_input_maps_main_claim_shape():
    claim = _build_claim(
        description="Va chạm nhẹ trong hầm xe, không có thương tích.",
        location_text="10.776900,106.700900",
        has_third_party=False,
    )
    vehicle = _build_vehicle()

    agent_incident = _build_agent_incident_input(claim=claim, vehicle=vehicle)

    assert agent_incident.time == "2026-03-20 20:15"
    assert agent_incident.location == "10.776900,106.700900"
    assert agent_incident.gps_coordinates == "10.776900,106.700900"
    assert agent_incident.insurer == "PTI"
    assert agent_incident.policy_id == "POL-001"
    assert agent_incident.policy_start_date == "2026-01-01"
    assert agent_incident.policy_end_date == "2026-12-31"
    assert agent_incident.vehicle_plate == "51K-12345"
    assert agent_incident.third_party_involved is False
    assert agent_incident.vehicle_drivable is False
    assert agent_incident.towing_required is True


def test_build_agent_incident_input_infers_highway_and_vehicle_count():
    claim = _build_claim(
        description="Tai nạn liên hoàn 3 xe trên cao tốc, cần giữ nguyên hiện trường.",
        location_text="Cao tốc Long Thành - Dầu Giây",
        has_third_party=True,
    )
    vehicle = _build_vehicle()

    agent_incident = _build_agent_incident_input(claim=claim, vehicle=vehicle)

    assert agent_incident.highway_incident is True
    assert agent_incident.number_of_vehicles_involved == 3
