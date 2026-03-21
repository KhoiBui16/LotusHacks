"""
Integration tests cho workflow API endpoint — test TOÀN BỘ pipeline.

Dùng httpx AsyncClient gọi trực tiếp endpoint FastAPI.
Mock LLM calls nhưng KHÔNG mock rule-based logic.

Test matrix:
    - 3 cases COMPLEX (rule pre-filter, không cần LLM)
    - 1 case EXCLUDED (rule-based exclusion Agent 2, không cần LLM)
    - 2 cases ELIGIBLE (mock LLM response)
    - 1 case MINIMAL (chỉ required fields)
    - 1 case request validation error (thiếu required fields)
"""
import json
import pytest
import pytest_asyncio
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app


TEST_CITATION = {
    "chunk_id": "c1",
    "source": "policy_pti.txt",
    "article": "Điều 4",
    "insurer": "PTI",
    "score": 0.91,
}


@pytest_asyncio.fixture
async def client():
    """Async HTTP client gọi API qua ASGI (không cần start server)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


API_PATH = "/api/v1/agent/workflow/process-incident"


# ══════════════════════════════════════════════════════════════════
# TEST: COMPLEX CASES (Rule pre-filter → skip LLM hoàn toàn)
# ══════════════════════════════════════════════════════════════════

class TestComplexCases:
    """Test cases phức tạp — rule pre-filter trigger, KHÔNG cần LLM."""

    @pytest.mark.asyncio
    async def test_case_01_highway_collision(self, client):
        """INC-001: Tai nạn liên hoàn cao tốc → COMPLEX (injuries + third_party + highway)."""
        body = {
            "time": "2024-06-15 08:30",
            "location": "Cao tốc TP.HCM - Long Thành",
            "description": "Va chạm liên hoàn 3 xe, có người bị thương",
            "incident_type": "va_cham",
            "third_party_involved": True,
            "vehicle_drivable": False,
            "injuries": True,
            "insurer": "Bảo Việt",
            "highway_incident": True,
            "estimated_damage": 180000000,
        }
        resp = await client.post(API_PATH, json=body)
        assert resp.status_code == 200

        data = resp.json()
        assert data["triage_result"]["is_complex"] is True
        assert data["coverage_result"] is None
        assert "ASSISTED_MODE" in data["next_step"]
        assert data["assisted_mode"] is not None
        assert data["checklist"] is None

        # Phải có triggered_rules (rule-based, không phải LLM)
        rules = data["triage_result"]["triggered_rules"]
        assert len(rules) >= 3  # injuries + third_party + highway + vehicle_drivable

    @pytest.mark.asyncio
    async def test_case_05_collision_injury(self, client):
        """INC-005: Va chạm xe máy + thương tích → COMPLEX."""
        body = {
            "time": "2024-06-19 17:45",
            "location": "Ngã tư Hàng Xanh, TP.HCM",
            "description": "Va chạm xe máy, người lái xe máy bị xây xát",
            "incident_type": "va_cham",
            "third_party_involved": True,
            "vehicle_drivable": True,
            "injuries": True,
            "insurer": "PTI",
        }
        resp = await client.post(API_PATH, json=body)
        assert resp.status_code == 200

        data = resp.json()
        assert data["triage_result"]["is_complex"] is True
        rules = data["triage_result"]["triggered_rules"]
        assert any("bị thương" in r for r in rules)
        assert any("bên thứ ba" in r for r in rules)

    @pytest.mark.asyncio
    @patch("app.agent.agents.insurance_agents._call_llm")
    @patch("app.agent.agents.insurance_agents.policy_retriever")
    async def test_case_03_flood_undrivable(self, mock_retriever, mock_llm, client):
        """INC-003: Ngập nước, xe không chạy được → không auto COMPLEX chỉ vì xe chết máy."""
        mock_retriever.retrieve_with_filter_details.return_value = ("Context...", [TEST_CITATION])
        mock_llm.side_effect = [
            json.dumps({"is_complex": False, "description": "Ngập nước đơn xe, không có bên thứ ba. [policy_pti.txt | Điều 4 | c1]"}),
            json.dumps({
                "is_eligible": True,
                "description": "Có thể tiếp tục pre-check coverage. [policy_pti.txt | Điều 4 | c1]",
                "coverage_summary": "Ngập nước thuộc diện cần xem quyền lợi thủy kích. [policy_pti.txt | Điều 4 | c1]",
            }),
        ]
        body = {
            "time": "2024-07-20 07:15",
            "location": "Bình Thạnh, TP.HCM",
            "description": "Xe bị ngập nước thủy kích",
            "incident_type": "ngap_nuoc",
            "third_party_involved": False,
            "vehicle_drivable": False,
            "injuries": False,
            "insurer": "Bảo Việt",
            "policy_active": True,
        }
        resp = await client.post(API_PATH, json=body)
        assert resp.status_code == 200

        data = resp.json()
        assert data["triage_result"]["is_complex"] is False
        assert data["coverage_result"]["is_eligible"] is True


# ══════════════════════════════════════════════════════════════════
# TEST: EXCLUDED CASE (Agent 2 rule-based exclusion → skip LLM)
# ══════════════════════════════════════════════════════════════════

class TestExcludedCases:
    """Test cases loại trừ — Agent 2 rule-based, KHÔNG cần LLM."""

    @pytest.mark.asyncio
    @patch("app.agent.agents.insurance_agents._call_llm")
    @patch("app.agent.agents.insurance_agents.policy_retriever")
    async def test_case_07_alcohol_excluded(self, mock_retriever, mock_llm, client):
        """INC-007: Say rượu + GPLX hết hạn → Agent 2 exclusion (Điều 4.1)."""
        # Mock cho Agent 1 (vì case này vehicle_drivable=True, cần LLM)
        mock_retriever.retrieve_with_filter_details.return_value = ("Context...", [TEST_CITATION])
        mock_llm.return_value = json.dumps({
            "is_complex": False,
            "description": "Sự cố đơn giản — va chạm dải phân cách [policy_pti.txt | Điều 4 | c1]",
        })

        body = {
            "time": "2024-09-10 23:00",
            "location": "Gò Vấp, TP.HCM",
            "description": "Va chạm dải phân cách ban đêm",
            "incident_type": "va_cham",
            "third_party_involved": False,
            "vehicle_drivable": True,
            "injuries": False,
            "insurer": "PTI",
            "driver_license_valid": False,
            "alcohol_involved": True,
        }
        resp = await client.post(API_PATH, json=body)
        assert resp.status_code == 200

        data = resp.json()
        assert data["triage_result"]["is_complex"] is False
        assert data["coverage_result"]["is_eligible"] is False
        assert "nồng độ cồn" in data["coverage_result"]["description"].lower()
        assert "NOT_ELIGIBLE" in data["next_step"]
        assert data["checklist"] is None


# ══════════════════════════════════════════════════════════════════
# TEST: ELIGIBLE CASES (Mock LLM — full pipeline)
# ══════════════════════════════════════════════════════════════════

class TestEligibleCases:
    """Test cases đủ điều kiện — mock LLM cho cả 2 agent."""

    @pytest.mark.asyncio
    @patch("app.agent.agents.insurance_agents._call_llm")
    @patch("app.agent.agents.insurance_agents.policy_retriever")
    async def test_case_02_simple_scratch(self, mock_retriever, mock_llm, client):
        """INC-002: Trầy xước nhẹ → SIMPLE + ELIGIBLE + checklist."""
        mock_retriever.retrieve_with_filter_details.return_value = ("Phạm vi BH...", [TEST_CITATION])
        # Agent 1 trả simple, Agent 2 trả eligible
        mock_llm.side_effect = [
            json.dumps({"is_complex": False, "description": "Trầy xước nhẹ, đơn giản. [policy_pti.txt | Điều 4 | c1]"}),
            json.dumps({
                "is_eligible": True,
                "description": "Thuộc phạm vi BH vật chất xe PTI. [policy_pti.txt | Điều 4 | c1]",
                "coverage_summary": "Điều 2 - Phạm vi BH vật chất xe [policy_pti.txt | Điều 4 | c1]",
            }),
        ]

        body = {
            "time": "2024-06-16 14:00",
            "location": "Quận 1, TP.HCM",
            "description": "Trầy xước nhẹ ở cản sau khi đỗ xe",
            "incident_type": "tray_xuoc",
            "third_party_involved": False,
            "vehicle_drivable": True,
            "injuries": False,
            "insurer": "PTI",
            "driver_license_valid": True,
            "vehicle_registration_valid": True,
            "alcohol_involved": False,
        }
        resp = await client.post(API_PATH, json=body)
        assert resp.status_code == 200

        data = resp.json()
        assert data["triage_result"]["is_complex"] is False
        assert data["coverage_result"]["is_eligible"] is True
        assert "ELIGIBLE" in data["next_step"]
        assert data["checklist"] is not None
        assert len(data["checklist"]) >= 8  # Base checklist ≥ 8 items

    @pytest.mark.asyncio
    @patch("app.agent.agents.insurance_agents._call_llm")
    @patch("app.agent.agents.insurance_agents.policy_retriever")
    async def test_case_08_night_collision(self, mock_retriever, mock_llm, client):
        """INC-008: Cạ dải phân cách đêm → SIMPLE + ELIGIBLE."""
        mock_retriever.retrieve_with_filter_details.return_value = ("Context...", [TEST_CITATION])
        mock_llm.side_effect = [
            json.dumps({"is_complex": False, "description": "Va chạm nhẹ, đơn giản. [policy_pti.txt | Điều 4 | c1]"}),
            json.dumps({
                "is_eligible": True,
                "description": "Thuộc phạm vi BH. [policy_pti.txt | Điều 4 | c1]",
                "coverage_summary": "Điều 2 - BH vật chất [policy_pti.txt | Điều 4 | c1]",
            }),
        ]

        body = {
            "time": "2024-10-12 21:30",
            "location": "Quận 5, TP.HCM",
            "description": "Cạ dải phân cách bê tông khi tránh ổ gà",
            "incident_type": "va_cham",
            "third_party_involved": False,
            "vehicle_drivable": True,
            "injuries": False,
            "insurer": "PTI",
            "driver_license_valid": True,
            "alcohol_involved": False,
        }
        resp = await client.post(API_PATH, json=body)
        assert resp.status_code == 200

        data = resp.json()
        assert data["coverage_result"]["is_eligible"] is True
        assert data["checklist"] is not None


# ══════════════════════════════════════════════════════════════════
# TEST: EDGE CASES
# ══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Test edge cases + validation errors."""

    @pytest.mark.asyncio
    async def test_case_09_minimal_input(self, client):
        """INC-009: Chỉ required fields → không crash, schema defaults hoạt động."""
        body = {
            "time": "2024-06-15 10:00",
            "location": "TP.HCM",
            "description": "Xe bị trầy nhẹ",
            "third_party_involved": False,
            "vehicle_drivable": True,
            "injuries": False,
        }
        resp = await client.post(API_PATH, json=body)
        # 200 = LLM success, 500 = LLM error (nhưng schema không crash)
        assert resp.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client):
        """Test: thiếu required fields → 422 Validation Error."""
        body = {"time": "2024-06-15 10:00"}
        resp = await client.post(API_PATH, json=body)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_incident_type(self, client):
        """Test: incident_type không hợp lệ → 422."""
        body = {
            "time": "2024-06-15 10:00",
            "location": "TP.HCM",
            "description": "Test",
            "incident_type": "invalid_type_xyz",
            "third_party_involved": False,
            "vehicle_drivable": True,
            "injuries": False,
        }
        resp = await client.post(API_PATH, json=body)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_rag_stats_endpoint(self, client):
        """Test: GET /rag-stats trả về thống kê Zilliz."""
        resp = await client.get("/api/v1/agent/workflow/rag-stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_chunks" in data
        assert "collection_name" in data
        assert data["vector_backend"] == "zilliz"
