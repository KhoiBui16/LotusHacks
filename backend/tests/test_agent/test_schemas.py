"""
Unit tests cho Agent Pydantic schemas.
"""
import pytest
from pydantic import ValidationError
from app.agent.models.schemas import IncidentInput, TriageOutput, CoverageOutput, WorkflowResponse


class TestIncidentInput:
    """Test IncidentInput schema validation."""

    def test_valid_input(self, sample_incident_simple):
        """Test tạo IncidentInput hợp lệ."""
        incident = IncidentInput(**sample_incident_simple)
        assert incident.location == "Quận 1, TP.HCM"
        assert incident.injuries is False
        assert incident.vehicle_drivable is True

    def test_valid_complex_input(self, sample_incident_complex):
        """Test tạo IncidentInput phức tạp."""
        incident = IncidentInput(**sample_incident_complex)
        assert incident.third_party_involved is True
        assert incident.injuries is True
        assert incident.insurer == "Bảo Việt"

    def test_missing_required_field(self):
        """Test thiếu trường bắt buộc → ValidationError."""
        with pytest.raises(ValidationError):
            IncidentInput(time="2024-06-16", location="HCM")

    def test_optional_fields_default(self):
        """Test các trường optional có giá trị mặc định."""
        incident = IncidentInput(
            time="2024-06-16 14:00",
            location="HCM",
            description="Test",
            incident_type="khac",
            third_party_involved=False,
            vehicle_drivable=True,
            injuries=False,
        )
        assert incident.insurer is None or incident.insurer == ""


class TestTriageOutput:
    """Test TriageOutput schema."""

    def test_complex_output(self):
        """Test output sự cố phức tạp."""
        output = TriageOutput(is_complex=True, description="Tai nạn liên hoàn")
        assert output.is_complex is True
        assert "liên hoàn" in output.description
        assert output.citations == []

    def test_simple_output(self):
        """Test output sự cố đơn giản."""
        output = TriageOutput(is_complex=False, description="Trầy xước nhẹ")
        assert output.is_complex is False


class TestCoverageOutput:
    """Test CoverageOutput schema."""

    def test_eligible(self):
        """Test output đủ điều kiện bồi thường."""
        output = CoverageOutput(is_eligible=True, description="Thuộc phạm vi bảo hiểm")
        assert output.is_eligible is True
        assert output.citations == []

    def test_not_eligible(self):
        """Test output không đủ điều kiện."""
        output = CoverageOutput(is_eligible=False, description="Bị loại trừ")
        assert output.is_eligible is False


class TestWorkflowResponse:
    """Test WorkflowResponse schema."""

    def test_complex_workflow(self):
        """Test workflow response cho sự cố phức tạp (chỉ có triage, không có coverage)."""
        triage = TriageOutput(is_complex=True, description="Phức tạp")
        response = WorkflowResponse(
            triage_result=triage,
            coverage_result=None,
            next_step="ASSISTED_MODE",
            assisted_mode={"hotline": "113"}
        )
        assert response.triage_result.is_complex is True
        assert response.coverage_result is None
        assert "ASSISTED" in response.next_step

    def test_simple_eligible_workflow(self):
        """Test workflow response cho sự cố đơn giản + đủ điều kiện."""
        triage = TriageOutput(is_complex=False, description="Đơn giản")
        coverage = CoverageOutput(is_eligible=True, description="OK")
        response = WorkflowResponse(
            triage_result=triage,
            coverage_result=coverage,
            next_step="ELIGIBLE",
            assisted_mode=None
        )
        assert response.triage_result.is_complex is False
        assert response.coverage_result.is_eligible is True
