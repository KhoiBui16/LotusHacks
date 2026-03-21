"""
Unit tests cho Insurance Agents (Triage + Coverage).

Mock LLM calls để test logic mà không cần API key thật.
Test coverage:
    - JSON parsing từ LLM response
    - Agent 1: Rule-based pre-filter (complex detection, skip LLM)
    - Agent 1: LLM classify (mock)
    - Agent 1: LLM error fallback
    - Agent 2: Rule-based exclusion check (skip LLM)
    - Agent 2: LLM eligible / not eligible (mock)
    - Agent 2: LLM error fallback
    - RAG context cache giữa Agent 1 → Agent 2
    - Workflow pipeline end-to-end (mock)
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from app.agent.models.schemas import IncidentInput, TriageOutput, CoverageOutput
from app.agent.agents.insurance_agents import (
    InsuranceAgents,
    _parse_json_response,
    _call_llm,
)


TEST_CITATION = {
    "chunk_id": "c1",
    "source": "policy_pti.txt",
    "article": "Điều 4",
    "insurer": "PTI",
    "score": 0.91,
}


# ══════════════════════════════════════════════════════════════════
# TEST JSON PARSING
# ══════════════════════════════════════════════════════════════════

class TestParseJsonResponse:
    """Test _parse_json_response() — parse JSON từ LLM response."""

    def test_parse_clean_json(self):
        """Test parse JSON thuần (không có markdown wrapper)."""
        content = '{"is_complex": true, "description": "Test"}'
        result = _parse_json_response(content)
        assert result["is_complex"] is True

    def test_parse_json_with_markdown(self):
        """Test parse JSON wrapped trong ```json ... ```."""
        content = '```json\n{"is_complex": false, "description": "OK"}\n```'
        result = _parse_json_response(content)
        assert result["is_complex"] is False

    def test_parse_json_with_generic_codeblock(self):
        """Test parse JSON wrapped trong generic ``` ... ```."""
        content = '```\n{"is_eligible": true, "description": "Eligible"}\n```'
        result = _parse_json_response(content)
        assert result["is_eligible"] is True

    def test_parse_invalid_json(self):
        """Test parse JSON không hợp lệ → raise json.JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            _parse_json_response("This is not JSON")


# ══════════════════════════════════════════════════════════════════
# TEST AGENT 1: TRIAGE AGENT
# ══════════════════════════════════════════════════════════════════

class TestTriageAgent:
    """Test Agent 1 (Triage Agent) — phân loại sự cố."""

    def test_triage_rule_based_complex_injuries(self, sample_incident_complex):
        """
        Test: Rule-based pre-filter — injuries=True → is_complex=True.
        Không cần mock LLM vì rule-based skip LLM hoàn toàn.
        """
        agents = InsuranceAgents()
        incident = IncidentInput(**sample_incident_complex)
        result = agents.run_triage_agent(incident)

        assert isinstance(result, TriageOutput)
        assert result.is_complex is True
        assert len(result.triggered_rules) > 0
        assert any("bị thương" in r for r in result.triggered_rules)

    def test_triage_rule_based_complex_third_party(self):
        """Test: Rule-based pre-filter — third_party=True → is_complex=True."""
        agents = InsuranceAgents()
        incident = IncidentInput(
            time="2024-06-15 08:30",
            location="TP.HCM",
            description="Va chạm với xe máy",
            incident_type="va_cham",
            third_party_involved=True,
            vehicle_drivable=True,
            injuries=False,
        )
        result = agents.run_triage_agent(incident)

        assert result.is_complex is True
        assert any("bên thứ ba" in r for r in result.triggered_rules)

    def test_triage_rule_based_complex_highway(self):
        """Test: Rule-based pre-filter — highway_incident=True → is_complex=True."""
        agents = InsuranceAgents()
        incident = IncidentInput(
            time="2024-06-15 08:30",
            location="Cao tốc HCM-LT",
            description="Va chạm trên cao tốc",
            incident_type="va_cham",
            third_party_involved=False,
            vehicle_drivable=True,
            injuries=False,
            highway_incident=True,
        )
        result = agents.run_triage_agent(incident)

        assert result.is_complex is True
        assert any("cao tốc" in r for r in result.triggered_rules)

    def test_triage_rule_based_complex_multi_vehicle(self):
        """Test: Rule-based pre-filter — từ 3 xe trở lên → is_complex=True."""
        agents = InsuranceAgents()
        incident = IncidentInput(
            time="2024-06-15 08:30",
            location="TP.HCM",
            description="Va chạm liên hoàn nhiều xe",
            incident_type="va_cham",
            third_party_involved=False,
            vehicle_drivable=True,
            injuries=False,
            number_of_vehicles_involved=3,
        )
        result = agents.run_triage_agent(incident)

        assert result.is_complex is True
        assert any("3 xe" in r or "liên hoàn" in r for r in result.triggered_rules)

    @patch("app.agent.agents.insurance_agents._call_llm")
    @patch("app.agent.agents.insurance_agents.policy_retriever")
    def test_triage_simple_incident_llm(self, mock_retriever, mock_llm, sample_incident_simple):
        """
        Test: Sự cố đơn giản → rule-based KHÔNG trigger → gọi LLM.
        Mock LLM trả về is_complex=False.
        """
        mock_retriever.retrieve_with_filter_details.return_value = ("Phạm vi bảo hiểm...", [TEST_CITATION])
        mock_llm.return_value = json.dumps({
            "is_complex": False,
            "description": "Trầy xước nhẹ, không có bên thứ ba. [policy_pti.txt | Điều 4 | c1]",
        })

        agents = InsuranceAgents()
        incident = IncidentInput(**sample_incident_simple)
        result = agents.run_triage_agent(incident)

        assert isinstance(result, TriageOutput)
        assert result.is_complex is False
        assert result.triggered_rules == []  # LLM classify, not rule-based
        assert len(result.citations) == 1

    @patch("app.agent.agents.insurance_agents._call_llm")
    @patch("app.agent.agents.insurance_agents.policy_retriever")
    def test_triage_llm_error_fallback(self, mock_retriever, mock_llm, sample_incident_simple):
        """
        Test: LLM lỗi → fallback is_complex=True (an toàn).
        Đảm bảo service không crash khi OpenAI/Qwen unavailable.
        """
        mock_retriever.retrieve_with_filter_details.return_value = ("Context...", [TEST_CITATION])
        mock_llm.side_effect = Exception("API Error")

        agents = InsuranceAgents()
        incident = IncidentInput(**sample_incident_simple)
        result = agents.run_triage_agent(incident)

        assert isinstance(result, TriageOutput)
        assert result.is_complex is True  # Fallback: mặc định phức tạp
        assert "Fallback" in result.description
        assert len(result.citations) == 1


# ══════════════════════════════════════════════════════════════════
# TEST AGENT 2: COVERAGE AGENT
# ══════════════════════════════════════════════════════════════════

class TestCoverageAgent:
    """Test Agent 2 (Coverage Agent) — kiểm tra eligibility."""

    def test_coverage_policy_inactive(self):
        """Test: Policy inactive → NOT ELIGIBLE trước khi cần LLM."""
        agents = InsuranceAgents()
        incident = IncidentInput(
            time="2024-06-15 08:30",
            location="TP.HCM",
            description="Xe bị trầy nhẹ",
            incident_type="tray_xuoc",
            third_party_involved=False,
            vehicle_drivable=True,
            injuries=False,
            insurer="PTI",
            policy_active=False,
        )
        result = agents.run_coverage_agent(incident)

        assert isinstance(result, CoverageOutput)
        assert result.is_eligible is False
        assert "hiệu lực" in result.description.lower()

    def test_coverage_excluded_alcohol(self, sample_incident_excluded):
        """
        Test: Rule-based exclusion — alcohol_involved=True → is_eligible=False.
        Không cần mock LLM vì rule-based skip LLM hoàn toàn.
        """
        agents = InsuranceAgents()
        incident = IncidentInput(**sample_incident_excluded)
        result = agents.run_coverage_agent(incident)

        assert isinstance(result, CoverageOutput)
        assert result.is_eligible is False
        assert "nồng độ cồn" in result.description.lower()

    def test_coverage_excluded_invalid_license(self):
        """Test: Rule-based exclusion — driver_license_valid=False → NOT ELIGIBLE."""
        agents = InsuranceAgents()
        incident = IncidentInput(
            time="2024-06-15 08:30",
            location="TP.HCM",
            description="Xe bị móp",
            incident_type="va_cham",
            third_party_involved=False,
            vehicle_drivable=True,
            injuries=False,
            driver_license_valid=False,
            alcohol_involved=False,
        )
        result = agents.run_coverage_agent(incident)

        assert result.is_eligible is False
        assert "GPLX" in result.description

    def test_coverage_excluded_invalid_registration(self):
        """Test: Rule-based exclusion — vehicle_registration_valid=False → NOT ELIGIBLE."""
        agents = InsuranceAgents()
        incident = IncidentInput(
            time="2024-06-15 08:30",
            location="TP.HCM",
            description="Xe bị trầy",
            incident_type="tray_xuoc",
            third_party_involved=False,
            vehicle_drivable=True,
            injuries=False,
            vehicle_registration_valid=False,
            alcohol_involved=False,
        )
        result = agents.run_coverage_agent(incident)

        assert result.is_eligible is False
        assert "đăng kiểm" in result.description.lower()

    @patch("app.agent.agents.insurance_agents._call_llm")
    @patch("app.agent.agents.insurance_agents.policy_retriever")
    def test_coverage_eligible(self, mock_retriever, mock_llm, sample_incident_simple):
        """Test: Sự cố đủ điều kiện → LLM trả về is_eligible=True."""
        mock_retriever.retrieve_with_filter_details.return_value = (
            "Phạm vi bảo hiểm: va chạm...",
            [TEST_CITATION],
        )
        mock_llm.return_value = json.dumps({
            "is_eligible": True,
            "description": "Thuộc phạm vi bảo hiểm vật chất xe. [policy_pti.txt | Điều 4 | c1]",
            "coverage_summary": "Điều 2 - Phạm vi BH vật chất xe, PTI [policy_pti.txt | Điều 4 | c1]",
        })

        agents = InsuranceAgents()
        incident = IncidentInput(**sample_incident_simple)
        result = agents.run_coverage_agent(incident)

        assert isinstance(result, CoverageOutput)
        assert result.is_eligible is True
        assert result.coverage_summary is not None
        assert len(result.citations) == 1

    @patch("app.agent.agents.insurance_agents._call_llm")
    @patch("app.agent.agents.insurance_agents.policy_retriever")
    def test_coverage_not_eligible(self, mock_retriever, mock_llm, sample_incident_simple):
        """Test: Sự cố không đủ điều kiện (LLM đánh giá bị loại trừ)."""
        mock_retriever.retrieve_with_filter_details.return_value = (
            "Loại trừ: trầy xước tự gây...",
            [TEST_CITATION],
        )
        mock_llm.return_value = json.dumps({
            "is_eligible": False,
            "description": "Trầy xước tự gây không thuộc phạm vi bảo hiểm. [policy_pti.txt | Điều 4 | c1]",
            "coverage_summary": None,
        })

        agents = InsuranceAgents()
        incident = IncidentInput(**sample_incident_simple)
        result = agents.run_coverage_agent(incident)

        assert isinstance(result, CoverageOutput)
        assert result.is_eligible is False
        assert len(result.citations) == 1

    @patch("app.agent.agents.insurance_agents._call_llm")
    @patch("app.agent.agents.insurance_agents.policy_retriever")
    def test_coverage_llm_error_fallback(self, mock_retriever, mock_llm, sample_incident_simple):
        """Test: LLM lỗi → fallback is_eligible=False (an toàn)."""
        mock_retriever.retrieve_with_filter_details.return_value = ("Context...", [TEST_CITATION])
        mock_llm.side_effect = Exception("API Error")

        agents = InsuranceAgents()
        incident = IncidentInput(**sample_incident_simple)
        result = agents.run_coverage_agent(incident)

        assert isinstance(result, CoverageOutput)
        assert result.is_eligible is False  # Fallback: mặc định không đủ
        assert "Fallback" in result.description
        assert len(result.citations) == 1


# ══════════════════════════════════════════════════════════════════
# TEST RAG CONTEXT CACHE
# ══════════════════════════════════════════════════════════════════

class TestRagContextCache:
    """Test in-memory RAG context cache giữa Agent 1 → Agent 2 với retriever Zilliz."""

    @patch("app.agent.agents.insurance_agents._call_llm")
    @patch("app.agent.agents.insurance_agents.policy_retriever")
    def test_cache_created_after_triage(self, mock_retriever, mock_llm, sample_incident_simple):
        """Test: Agent 1 lưu RAG context vào cache sau khi query."""
        mock_retriever.retrieve_with_filter_details.return_value = ("Cached context...", [TEST_CITATION])
        mock_llm.return_value = json.dumps({
            "is_complex": False,
            "description": "Đơn giản",
        })

        agents = InsuranceAgents()
        agents._rag_cache = {}  # Reset cache
        incident = IncidentInput(**sample_incident_simple)
        agents.run_triage_agent(incident)

        # Kiểm tra cache có data
        assert len(agents._rag_cache) > 0, "RAG cache phải có ít nhất 1 entry sau triage"


# ══════════════════════════════════════════════════════════════════
# TEST SCHEMAS VALIDATION
# ══════════════════════════════════════════════════════════════════

class TestSchemas:
    """Test Pydantic schema validation cho IncidentInput."""

    def test_incident_input_required_fields(self):
        """Test: IncidentInput với chỉ required fields."""
        incident = IncidentInput(
            time="2024-06-15 08:30",
            location="TP.HCM",
            description="Test",
            third_party_involved=False,
            vehicle_drivable=True,
            injuries=False,
        )
        assert incident.time == "2024-06-15 08:30"
        assert incident.incident_type.value == "khac"  # default
        assert incident.driver_license_valid is None  # optional, default None
        assert incident.alcohol_involved is None

    def test_incident_input_all_fields(self, sample_incident_complex):
        """Test: IncidentInput với các field làm giàu cho workflow hiện tại."""
        incident = IncidentInput(**sample_incident_complex)
        assert incident.driver_license_valid is True
        assert incident.vehicle_registration_valid is True
        assert incident.alcohol_involved is False
        assert incident.highway_incident is True

    def test_triage_output_with_triggered_rules(self):
        """Test: TriageOutput với triggered_rules (audit trail)."""
        output = TriageOutput(
            is_complex=True,
            description="Phức tạp",
            triggered_rules=["Có người bị thương", "Trên cao tốc"],
        )
        assert len(output.triggered_rules) == 2

    def test_triage_output_default_triggered_rules(self):
        """Test: TriageOutput triggered_rules default = empty list."""
        output = TriageOutput(
            is_complex=False,
            description="Đơn giản",
        )
        assert output.triggered_rules == []
        assert output.citations == []

    def test_coverage_output_with_summary(self):
        """Test: CoverageOutput với coverage_summary."""
        output = CoverageOutput(
            is_eligible=True,
            description="Đủ điều kiện",
            coverage_summary="Điều 2 - Phạm vi BH vật chất xe",
        )
        assert output.coverage_summary is not None
        assert output.citations == []

    def test_coverage_output_default_summary(self):
        """Test: CoverageOutput coverage_summary default = None."""
        output = CoverageOutput(
            is_eligible=False,
            description="Loại trừ",
        )
        assert output.coverage_summary is None
        assert output.citations == []
