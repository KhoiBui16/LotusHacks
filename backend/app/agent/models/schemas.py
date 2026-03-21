"""
Pydantic schemas cho workflow 2-agent giai đoạn mục tiêu.

Trọng tâm hiện tại:
    - Agent 1 (Triage): phân loại case PHỨC TẠP / KHÔNG PHỨC TẠP
    - Agent 2 (Coverage pre-check): phân loại ĐỦ / KHÔNG ĐỦ điều kiện sơ bộ

Schema được giữ thiên về input thực tế từ app/AI interview, không áp đặt
taxonomy retrieval lên policy chunks. RAG sẽ chỉ đóng vai trò truy xuất
context/citation để agent đối chiếu với input người dùng.
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class IncidentType(str, Enum):
    """Loại sự cố người dùng chọn ở bước E1."""

    COLLISION = "va_cham"
    SCRATCH = "tray_xuoc"
    GLASS_BREAK = "vo_kinh"
    FLOOD = "ngap_nuoc"
    THEFT = "mat_cap"
    OTHER = "khac"


class IncidentInput(BaseModel):
    """
    Input chung cho 2 agent.

    Nhóm trường chính:
        1. Incident intake (E2A-E2F)
        2. Policy linkage / policy validity
        3. Vehicle & driver information
        4. Rich context để Agent 1/2 suy luận tốt hơn
    """

    # E2A-E2F: core input từ AI interview
    time: str = Field(..., description="Thời gian xảy ra sự cố.")
    location: str = Field(..., description="Địa điểm xảy ra sự cố.")
    description: str = Field(..., description="Mô tả tự do của người dùng.")
    incident_type: IncidentType = Field(
        default=IncidentType.OTHER,
        description="Loại sự cố user chọn ở bước intake.",
    )
    third_party_involved: bool = Field(
        ...,
        description="Có bên thứ ba liên quan không.",
    )
    vehicle_drivable: bool = Field(
        ...,
        description="Xe còn tự di chuyển được không.",
    )
    injuries: bool = Field(
        ...,
        description="Có người bị thương / tử vong không.",
    )

    # Policy linkage / coverage pre-check
    policy_id: Optional[str] = Field(
        None,
        description="Mã hợp đồng hoặc mã policy liên kết với xe.",
    )
    insurer: Optional[str] = Field(
        None,
        description="Tên công ty bảo hiểm nếu đã biết.",
    )
    policy_active: Optional[bool] = Field(
        None,
        description="Cờ nhanh cho biết policy còn hiệu lực hay không.",
    )
    policy_start_date: Optional[str] = Field(
        None,
        description="Ngày bắt đầu hiệu lực policy (ISO-like string).",
    )
    policy_end_date: Optional[str] = Field(
        None,
        description="Ngày hết hiệu lực policy (ISO-like string).",
    )

    # Vehicle / driver
    vehicle_plate: Optional[str] = Field(None, description="Biển số xe.")
    vehicle_model: Optional[str] = Field(None, description="Dòng xe / đời xe.")
    driver_name: Optional[str] = Field(None, description="Tên người điều khiển xe.")
    driver_phone: Optional[str] = Field(None, description="Số điện thoại người điều khiển.")
    driver_license: Optional[str] = Field(None, description="Số GPLX.")
    driver_license_valid: Optional[bool] = Field(
        None,
        description="GPLX còn hiệu lực và phù hợp loại xe không.",
    )
    vehicle_registration_valid: Optional[bool] = Field(
        None,
        description="Đăng kiểm / giấy tờ xe còn hiệu lực không.",
    )
    alcohol_involved: Optional[bool] = Field(
        None,
        description="Người lái có vi phạm nồng độ cồn không.",
    )

    # Context làm giàu cho triage và coverage
    gps_coordinates: Optional[str] = Field(
        None,
        description="Tọa độ GPS nếu app lấy được từ thiết bị.",
    )
    highway_incident: Optional[bool] = Field(
        None,
        description="Sự cố xảy ra trên cao tốc.",
    )
    number_of_vehicles_involved: Optional[int] = Field(
        None,
        description="Tổng số xe liên quan nếu xác định được.",
    )
    estimated_damage: Optional[float] = Field(
        None,
        description="Ước tính thiệt hại sơ bộ (VNĐ).",
    )
    damage_parts: List[str] = Field(
        default_factory=list,
        description="Danh sách bộ phận hư hỏng hoặc mất cắp.",
    )
    weather_condition: Optional[str] = Field(
        None,
        description="Điều kiện thời tiết khi xảy ra sự cố.",
    )
    road_condition: Optional[str] = Field(
        None,
        description="Điều kiện mặt đường / hiện trường.",
    )
    towing_required: Optional[bool] = Field(
        None,
        description="Có cần cứu hộ / kéo xe hay không.",
    )
    theft_scope: Optional[str] = Field(
        None,
        description="Nếu incident_type=mat_cap: bo_phan hoặc toan_bo.",
    )
    witnesses: List[str] = Field(
        default_factory=list,
        description="Nhân chứng hoặc người liên hệ liên quan.",
    )
    police_report: Optional[bool] = Field(
        False,
        description="Đã có công an / biên bản tiếp nhận sơ bộ chưa.",
    )
    photos_taken: Optional[bool] = Field(
        False,
        description="Đã có ảnh hiện trường / tổn thất chưa.",
    )
    notes: Optional[str] = Field(
        None,
        description="Ghi chú bổ sung từ user hoặc AI interview.",
    )


class PolicyCitation(BaseModel):
    """Metadata tối thiểu để trace chunk policy mà agent đã dùng."""

    chunk_id: Optional[str] = Field(None, description="ID chunk trong vector store.")
    source: Optional[str] = Field(None, description="Tên tài liệu nguồn.")
    article: Optional[str] = Field(None, description="Điều khoản trích được từ chunk.")
    insurer: Optional[str] = Field(None, description="Insurer gắn với tài liệu nguồn.")
    score: Optional[float] = Field(None, description="Similarity score từ retriever.")


class TriageOutput(BaseModel):
    """
    Output của Agent 1.

    `is_complex=True` nghĩa là case cần đi sang Assisted Mode.
    """

    is_complex: bool = Field(
        ...,
        description="True nếu case cần Assisted Mode.",
    )
    description: str = Field(
        ...,
        description="Lý do phân loại dựa trên input và policy context.",
    )
    triggered_rules: List[str] = Field(
        default_factory=list,
        description="Các rule chắc chắn đã kích hoạt trước khi cần LLM.",
    )
    citations: List[PolicyCitation] = Field(
        default_factory=list,
        description="Các chunk policy được dùng để đối chiếu / giải thích.",
    )


class CoverageOutput(BaseModel):
    """
    Output của Agent 2.

    `is_eligible=True` nghĩa là đủ điều kiện sơ bộ để đi tiếp Dynamic Checklist.
    """

    is_eligible: bool = Field(
        ...,
        description="True nếu đủ điều kiện sơ bộ để tiếp tục claim.",
    )
    description: str = Field(
        ...,
        description="Giải thích sơ bộ về hiệu lực, quyền lợi, loại trừ, miễn thường.",
    )
    coverage_summary: Optional[str] = Field(
        None,
        description="Tóm tắt ngắn điều khoản / kết luận coverage.",
    )
    citations: List[PolicyCitation] = Field(
        default_factory=list,
        description="Các chunk policy được dùng để đánh giá eligibility.",
    )


class WorkflowResponse(BaseModel):
    """Response tổng cho endpoint workflow giai đoạn hiện tại."""

    triage_result: TriageOutput = Field(
        ...,
        description="Kết quả Agent 1.",
    )
    coverage_result: Optional[CoverageOutput] = Field(
        None,
        description="Kết quả Agent 2; vắng khi case đi Assisted Mode.",
    )
    next_step: str = Field(
        ...,
        description="Mã/bản mô tả bước tiếp theo của workflow.",
    )
    assisted_mode: Optional[dict] = Field(
        None,
        description="Thông tin hỗ trợ khẩn cấp khi Agent 1 kết luận complex.",
    )
    checklist: Optional[List[str]] = Field(
        None,
        description="Checklist hồ sơ sơ bộ khi Agent 2 kết luận eligible.",
    )
