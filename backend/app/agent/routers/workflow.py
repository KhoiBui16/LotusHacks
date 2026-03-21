"""
API Router cho AI Agent Workflow.

Endpoints:
    POST /workflow/process-incident  — Xử lý sự cố qua pipeline 2 Agent
    GET  /workflow/rag-stats         — Thống kê RAG vectorstore (Zilliz)
    POST /workflow/index-policies    — Trigger re-index policy documents

Workflow pipeline:
    1. Agent 1 (Triage): Phân loại phức tạp/đơn giản
    2. Nếu phức tạp → Assisted Mode (response ngay)
    3. Nếu đơn giản → Agent 2 (Coverage): Kiểm tra eligibility
    4. Nếu eligible → Sinh dynamic checklist hồ sơ sơ bộ cho giai đoạn hiện tại
"""
from fastapi import APIRouter, HTTPException
from app.agent.models.schemas import (
    IncidentInput,
    IncidentType,
    WorkflowResponse,
    TriageOutput,
    CoverageOutput,
)
from app.agent.agents.insurance_agents import insurance_agents
from app.agent.rag.retriever import policy_retriever

router = APIRouter(prefix="/workflow", tags=["AI Agent Workflow"])


@router.post("/process-incident", response_model=WorkflowResponse)
async def process_incident(incident: IncidentInput):
    """
    Xử lý sự cố bảo hiểm qua pipeline 2 Agent.

    **Workflow:**
    1. Agent 1 (Triage): Phân loại sự cố → phức tạp / đơn giản
       - Rule-based pre-filter (fast path, không tốn API)
       - RAG + LLM classify (nếu rule không đủ)
    2. Nếu phức tạp → Assisted Mode (hotline + hướng dẫn khẩn cấp)
    3. Nếu đơn giản → Agent 2 (Coverage): Kiểm tra điều kiện bồi thường
       - Policy validity + rule-based exclusion check
       - RAG + LLM evaluate eligibility
    4. Nếu eligible → Sinh dynamic checklist hồ sơ sơ bộ

    **Input:** IncidentInput (thông tin sự cố từ user)
    **Output:** WorkflowResponse (kết quả 2 agent + bước tiếp theo + checklist)
    """
    # ── AGENT 1: TRIAGE ──────────────────────────────────────────
    try:
        triage_result = insurance_agents.run_triage_agent(incident)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent 1 (Triage) lỗi: {str(e)}"
        )

    # ── ROUTING: Phức tạp → Assisted Mode ────────────────────────
    if triage_result.is_complex:
        return WorkflowResponse(
            triage_result=triage_result,
            coverage_result=None,
            next_step=(
                "ASSISTED_MODE: Sự cố phức tạp. "
                "Hướng dẫn khẩn cấp + hotline + giữ hiện trường. "
                "Thu first notice tối thiểu + bằng chứng ban đầu. "
                "Chuyển theo dõi hồ sơ / phối hợp insurer."
            ),
            assisted_mode={
                "emergency_hotline": "113 (Công an) / 115 (Cấp cứu)",
                "insurer_hotline": _get_insurer_hotline(incident.insurer),
                "instructions": [
                    "Giữ nguyên hiện trường nếu có thể",
                    "Gọi cấp cứu 115 nếu có người bị thương",
                    "Gọi công an 113 nếu có bên thứ ba",
                    "Chụp ảnh hiện trường từ nhiều góc (tổng thể + cận cảnh)",
                    "Thu thập thông tin nhân chứng (tên + SĐT)",
                    "Không di chuyển xe trước khi công an đến (trừ trường hợp nguy hiểm)",
                    "Thông báo cho nhà bảo hiểm trong vòng 24 giờ",
                ],
            },
            checklist=None,  # Không sinh checklist cho sự cố phức tạp
        )

    # ── AGENT 2: COVERAGE PRE-CHECK ──────────────────────────────
    # Lấy session_id từ cache (nếu Agent 1 đã cache RAG context)
    session_id = insurance_agents.get_session_id_from_cache()

    try:
        coverage_result = insurance_agents.run_coverage_agent(
            incident, session_id=session_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent 2 (Coverage) lỗi: {str(e)}"
        )

    # ── ROUTING: Eligible → Checklist / Not Eligible → Cảnh báo ─
    if coverage_result.is_eligible:
        # Sinh dynamic checklist hồ sơ sơ bộ cho giai đoạn hiện tại
        checklist = _generate_checklist(
            incident.insurer,
            incident.incident_type,
            theft_scope=incident.theft_scope,
        )
        next_step = (
            "ELIGIBLE: Đủ điều kiện sơ bộ để claim. "
            "Vui lòng chuẩn bị hồ sơ theo checklist bên dưới "
            "và upload documents."
        )
    else:
        checklist = None
        next_step = (
            "NOT_ELIGIBLE: Cảnh báo — sự cố có nguy cơ bị từ chối bồi thường. "
            "Gợi ý: không nên làm hồ sơ claim / tự sửa chữa ngoài / "
            "lưu lại thông tin sự cố để tham khảo."
        )

    return WorkflowResponse(
        triage_result=triage_result,
        coverage_result=coverage_result,
        next_step=next_step,
        assisted_mode=None,
        checklist=checklist,
    )


@router.get("/rag-stats")
async def get_rag_stats():
    """
    Trả về thống kê Zilliz vectorstore.

    Returns:
        dict: {vector_backend, collection_name, total_chunks, zilliz_uri}
    """
    return policy_retriever.get_stats()


@router.post("/index-policies")
async def trigger_index_policies():
    """
    Trigger re-index policy documents vào Zilliz.

    Dùng khi thêm file policy mới vào thư mục data/ hoặc khi
    cần cập nhật chunk/article metadata.

    Returns:
        dict: {status: "ok", stats: {...}}
    """
    try:
        from app.agent.rag.index_policies import index_text_policies
        index_text_policies()
        return {"status": "ok", "stats": policy_retriever.get_stats()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index lỗi: {str(e)}")


# ══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def _get_insurer_hotline(insurer: str | None) -> str:
    """
    Trả về hotline của nhà bảo hiểm dựa trên tên.

    Args:
        insurer: Tên nhà bảo hiểm (VD: "Bảo Việt", "PTI").

    Returns:
        str: Số hotline hoặc message chung nếu không tìm thấy.
    """
    hotlines = {
        "Bảo Việt": "1800 599 945 (24/7)",
        "PTI": "1800 1567 (24/7)",
        "MIC": "1900 9466",
        "PVI": "1900 545 458",
        "Bảo Minh": "1900 558 891",
    }
    if insurer and insurer in hotlines:
        return hotlines[insurer]
    return "Liên hệ nhà bảo hiểm của bạn"


def _generate_checklist(
    insurer: str | None,
    incident_type: IncidentType | None,
    theft_scope: str | None = None,
) -> list[str]:
    """
    Sinh dynamic checklist hồ sơ bồi thường sơ bộ.

    Checklist được tùy chỉnh theo:
    1. Loại sự cố (incident_type) — mất cắp cần thêm đơn trình báo
    2. Nhà bảo hiểm (insurer) — form theo mẫu riêng

    Args:
        insurer: Tên nhà bảo hiểm (VD: "PTI", "Bảo Việt").
        incident_type: Loại sự cố (VD: IncidentType.THEFT).
        theft_scope: `bo_phan` hoặc `toan_bo` nếu là case mất cắp.

    Returns:
        list[str]: Danh sách các hồ sơ cần chuẩn bị theo thứ tự ưu tiên.
    """
    insurer_name = insurer or "nhà bảo hiểm"

    # ── Base checklist (Điều 7.1 — luôn có) ──────────────────────
    checklist = [
        f"Thông báo tổn thất và yêu cầu bồi thường (theo mẫu {insurer_name})",
        "Giấy chứng nhận bảo hiểm / Hợp đồng bảo hiểm",
        "Giấy đăng ký xe (bản sao có xác nhận)",
        "Giấy phép lái xe hợp lệ (bản sao có xác nhận)",
        "Giấy chứng nhận kiểm định an toàn kỹ thuật còn hiệu lực",
        "Ảnh tổng thể xe (4 góc)",
        "Ảnh cận cảnh vị trí hư hỏng / tổn thất",
        "Ảnh hiện trường sự cố (nếu có)",
    ]

    # ── Checklist bổ sung theo loại sự cố ────────────────────────
    if incident_type == IncidentType.THEFT and theft_scope == "toan_bo":
        # Điều 7.4 — Mất cắp / mất cướp toàn bộ xe
        checklist.extend([
            "Đơn trình báo mất trộm/mất cướp có xác nhận công an",
            "Quyết định khởi tố và điều tra hình sự (nếu có)",
            "Quyết định đình chỉ điều tra (nếu có)",
            "Khai báo mất giấy tờ trên xe có xác nhận công an (nếu có)",
        ])

    if incident_type == IncidentType.FLOOD:
        checklist.append("Xác nhận tình trạng thời tiết / thiên tai từ cơ quan chức năng (nếu có)")

    # ── Checklist tài liệu sửa chữa (Điều 7.1.3) ───────────────
    checklist.extend([
        "Hóa đơn VAT sửa chữa / thay thế phụ tùng",
        "Biên bản giám định thiệt hại (do nhà BH thực hiện)",
    ])

    return checklist
