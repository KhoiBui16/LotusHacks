"""
Insurance AI Agents Module — Core logic cho 2 Agent pipeline.

Agent 1 (Triage Agent):
    - Input:  IncidentInput từ user
    - Process: Rule-based pre-filter → RAG retrieval theo ngữ cảnh/policy → LLM classify
    - Output: TriageOutput {is_complex, description, triggered_rules}
    - Fallback: Nếu LLM lỗi → mặc định is_complex=True (an toàn)

Agent 2 (Coverage Agent):
    - Input:  IncidentInput + cached RAG context từ Agent 1
    - Process: Policy validity check → rule-based exclusion check → RAG (insurer-specific) → LLM evaluate
    - Output: CoverageOutput {is_eligible, description, coverage_summary}
    - Fallback: Nếu LLM lỗi → mặc định is_eligible=False (an toàn)

LLM Strategy:
    - Primary: OpenAI (gpt-4o-mini)
    - Fallback: Qwen (qwen-plus) nếu OpenAI lỗi/timeout

RAG Context Cache:
    - Agent 1 lưu RAG chunks vào in-memory dict (_rag_cache)
    - Agent 2 load cached chunks + query thêm insurer-specific chunks
    - Giảm latency bằng cách không query lại Zilliz hoàn toàn
"""
import json
import os
import uuid
from datetime import datetime

from openai import OpenAI

from app.core.config import agent_settings
from app.agent.rag.retriever import policy_retriever
from app.agent.models.schemas import IncidentInput, TriageOutput, CoverageOutput


# ══════════════════════════════════════════════════════════════════
# LLM CLIENT HELPERS
# ══════════════════════════════════════════════════════════════════

def _get_openai_client() -> OpenAI:
    """
    Tạo OpenAI client (primary LLM).

    Hỗ trợ cả OpenAI gốc và proxy (Manus, vLLM, LiteLLM...) thông qua
    biến môi trường OPENAI_BASE_URL.

    Returns:
        OpenAI: Client instance sẵn sàng gọi chat completions.
    """
    kwargs = {
        "api_key": agent_settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", ""),
    }
    if agent_settings.OPENAI_BASE_URL:
        kwargs["base_url"] = agent_settings.OPENAI_BASE_URL
    return OpenAI(**kwargs)


def _get_qwen_client() -> OpenAI:
    """
    Tạo Qwen client (fallback LLM).

    Qwen sử dụng OpenAI-compatible API nên dùng luôn OpenAI SDK
    với base_url trỏ sang Dashscope.

    Returns:
        OpenAI: Client instance cho Qwen API.
    """
    return OpenAI(
        api_key=agent_settings.QWEN_API_KEY or os.getenv("QWEN_API_KEY", ""),
        base_url=agent_settings.QWEN_BASE_URL,
    )


def _call_llm(prompt: str, model: str = None) -> str:
    """
    Gọi LLM với fallback strategy: OpenAI → Qwen.

    Thử gọi OpenAI trước. Nếu lỗi (API error, timeout, rate limit)
    và có QWEN_API_KEY → tự động fallback sang Qwen.

    Args:
        prompt: Prompt đầy đủ gửi cho LLM (đã có system + user message).
        model: Tên model override (mặc định từ config AGENT_LLM_MODEL).

    Returns:
        str: Nội dung response text từ LLM.

    Raises:
        Exception: Nếu cả OpenAI lẫn Qwen đều lỗi.
    """
    system_msg = "Bạn là chuyên gia bảo hiểm ô tô Việt Nam. Luôn trả lời bằng JSON hợp lệ."

    # ── Try 1: OpenAI (primary) ────────────────────────────────
    try:
        client = _get_openai_client()
        primary_model = model or agent_settings.AGENT_LLM_MODEL
        response = client.chat.completions.create(
            model=primary_model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
            temperature=agent_settings.AGENT_LLM_TEMPERATURE,
            max_tokens=1500,
        )
        return response.choices[0].message.content
    except Exception as openai_err:
        # ── Try 2: Qwen fallback ──────────────────────────────
        if agent_settings.QWEN_API_KEY:
            try:
                client = _get_qwen_client()
                fallback_model = agent_settings.FALLBACK_LLM_MODEL
                response = client.chat.completions.create(
                    model=fallback_model,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=agent_settings.AGENT_LLM_TEMPERATURE,
                    max_tokens=1500,
                )
                return response.choices[0].message.content
            except Exception as qwen_err:
                raise Exception(
                    f"Cả OpenAI lẫn Qwen đều lỗi. "
                    f"OpenAI: {openai_err}. Qwen: {qwen_err}"
                )
        # Không có Qwen key → raise lỗi OpenAI
        raise openai_err


def _parse_json_response(content: str) -> dict:
    """
    Parse JSON từ LLM response (hỗ trợ cả markdown code block).

    LLM đôi khi wrap JSON trong ```json ... ```. Function này tự động
    strip code block trước khi parse.

    Args:
        content: Raw response text từ LLM.

    Returns:
        dict: Parsed JSON object.

    Raises:
        json.JSONDecodeError: Nếu content không phải JSON hợp lệ.
    """
    # Loại bỏ markdown code block nếu có
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    return json.loads(content.strip())


INSURER_KEY_MAP = {
    "BẢO VIỆT": "BAOVIET",
    "BAO VIET": "BAOVIET",
    "PTI": "PTI",
    "MIC": "MIC",
    "PVI": "PVI",
    "BẢO MINH": "BAO_MINH",
    "BAO MINH": "BAO_MINH",
}


def _normalize_insurer_key(insurer: str | None) -> str | None:
    """Chuẩn hóa insurer name về metadata key đang index trong RAG."""
    if not insurer:
        return None

    insurer_upper = insurer.upper()
    return INSURER_KEY_MAP.get(insurer_upper, insurer_upper)


def _build_policy_filter(insurer: str | None = None) -> dict | None:
    """Ghép metadata filter cho retriever theo insurer nếu có."""
    insurer_key = _normalize_insurer_key(insurer)
    if not insurer_key:
        return None
    return {"insurer": insurer_key}


def _parse_datetime_safe(value: str | None) -> datetime | None:
    """Parse chuỗi datetime/date phổ biến từ app mà không làm workflow văng lỗi."""
    if not value:
        return None

    candidates = [
        value.strip(),
        value.strip().replace("Z", "+00:00"),
        value.strip().replace("/", "-"),
    ]
    patterns = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for candidate in candidates:
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            pass

        for pattern in patterns:
            try:
                return datetime.strptime(candidate, pattern)
            except ValueError:
                continue

    return None


def _infer_description_complexity(description: str | None) -> list[str]:
    """Heuristic rất hẹp cho các mô tả chắc chắn là case phức tạp."""
    description_lower = (description or "").lower()
    mapping = {
        "tai nạn liên hoàn": "Mô tả có dấu hiệu tai nạn liên hoàn",
        "liên hoàn": "Mô tả có dấu hiệu tai nạn liên hoàn",
        "nhiều xe": "Mô tả cho thấy nhiều xe liên quan",
        "cháy": "Mô tả cho thấy có cháy/nổ",
        "nổ": "Mô tả cho thấy có cháy/nổ",
        "kẹt người": "Mô tả cho thấy có người mắc kẹt",
    }

    triggered = []
    for keyword, reason in mapping.items():
        if keyword in description_lower and reason not in triggered:
            triggered.append(reason)
    return triggered


def _check_policy_validity(incident: IncidentInput) -> tuple[bool | None, str]:
    """
    Kiểm tra hiệu lực policy dựa trên field struct trước khi gọi LLM.

    Returns:
        tuple[bool | None, str]:
            - True: đã xác nhận policy hợp lệ
            - False: policy không hợp lệ
            - None: chưa đủ dữ liệu để kết luận
    """
    if incident.policy_active is False:
        return False, "Policy được đánh dấu là không còn hiệu lực."

    incident_time = _parse_datetime_safe(incident.time)
    start_time = _parse_datetime_safe(incident.policy_start_date)
    end_time = _parse_datetime_safe(incident.policy_end_date)
    if incident_time and start_time and end_time:
        if incident_time < start_time or incident_time > end_time:
            return False, (
                f"Thời điểm sự cố ({incident.time}) nằm ngoài hiệu lực policy "
                f"({incident.policy_start_date} -> {incident.policy_end_date})."
            )
        return True, "Thời điểm sự cố nằm trong thời gian hiệu lực policy."

    if incident.policy_active is True:
        return True, "Policy đang được đánh dấu còn hiệu lực."

    return None, "Chưa đủ dữ liệu ngày hiệu lực policy để kết luận."


def _dedupe_citations(citations: list[dict] | None) -> list[dict]:
    """Gộp citations trùng nhau giữa nhiều lượt retrieve."""
    citations = citations or []
    deduped = []
    seen = set()

    for citation in citations:
        key = (
            citation.get("chunk_id"),
            citation.get("source"),
            citation.get("article"),
        )
        if key in seen:
            continue

        seen.add(key)
        deduped.append(citation)

    return deduped


def _format_citation_tail(citations: list[dict] | None, limit: int = 3) -> str:
    """Format citation ngắn gọn để ghép vào description rule-based."""
    citations = citations or []
    if not citations:
        return ""

    parts = []
    for citation in citations[:limit]:
        source = citation.get("source") or "unknown"
        article = citation.get("article") or "không rõ điều"
        chunk_id = citation.get("chunk_id") or ""
        parts.append(f"{source} / {article} / {chunk_id}")

    return f" Dẫn chiếu policy: {'; '.join(parts)}."


def _retrieve_policy_context(
    query: str,
    where: dict | None,
    k: int,
) -> tuple[str, list[dict]]:
    """Retrieve context + citations, fallback từ filtered search sang toàn pool."""
    try:
        context, citations = policy_retriever.retrieve_with_filter_details(
            query=query,
            where=where,
            k=k,
        )
        if citations:
            return context, citations
    except Exception:
        pass

    try:
        return policy_retriever.retrieve_details(query=query, k=k)
    except Exception as exc:
        return f"[RAG] Không thể truy xuất policy context: {exc}", []


# ══════════════════════════════════════════════════════════════════
# INSURANCE AGENTS CLASS
# ══════════════════════════════════════════════════════════════════

class InsuranceAgents:
    """
    Lớp chứa logic cho 2 AI Agent trong workflow bồi thường bảo hiểm.

    Pipeline:
        IncidentInput → Agent 1 (Triage) → [if complex → stop]
                         → Agent 2 (Coverage) → WorkflowResponse

    Agent 1 (Triage Agent):
        - Rule-based pre-filter: Check injuries, third_party, highway, multi-vehicle
        - RAG: Query Zilliz theo semantic query + insurer nếu có
        - LLM: Classify {is_complex: bool, description: str}
        - Cache: Lưu RAG context vào _rag_cache cho Agent 2

    Agent 2 (Coverage Agent):
        - Rule-based validity/exclusion: Check policy validity, alcohol, GPLX, đăng kiểm
        - RAG: Load cached A1 context + query thêm insurer-specific chunks
        - LLM: Evaluate {is_eligible: bool, description: str, coverage_summary: str}

    Attributes:
        _rag_cache: In-memory dict lưu RAG context giữa 2 agent.
                    Key = session_id (UUID), Value = RAG context string.
    """

    # In-memory cache cho RAG context giữa Agent 1 → Agent 2
    _rag_cache: dict[str, dict] = {}

    # ================================================================
    # AGENT 1: TRIAGE AGENT (Policy + Rule Engine)
    # ================================================================
    def run_triage_agent(self, incident: IncidentInput) -> TriageOutput:
        """
        Agent 1: Phân loại sự cố thành Phức tạp hoặc Đơn giản.

        Pipeline:
            1. Rule-based pre-filter (fast path, không tốn API call):
               - third_party=True → phức tạp
               - highway_incident=True → phức tạp
               - number_of_vehicles_involved>=3 hoặc mô tả liên hoàn → phức tạp
            2. Nếu không trigger rule → RAG query semantic trên corpus policy/legal
            3. LLM classify với RAG context
            4. Cache RAG context cho Agent 2

        Args:
            incident: IncidentInput chứa thông tin sự cố từ user.

        Returns:
            TriageOutput: Gồm is_complex (bool), description (str),
                          triggered_rules (list[str]).
        """
        session_id = str(uuid.uuid4())

        # ── STEP 1: Rule-based pre-filter (fast path, skip LLM) ──
        triggered_rules = []
        if incident.third_party_involved:
            triggered_rules.append("Có bên thứ ba liên quan")
        if getattr(incident, 'highway_incident', None):
            triggered_rules.append("Xảy ra trên đường cao tốc")
        if (incident.number_of_vehicles_involved or 0) >= 3:
            triggered_rules.append("Có từ 3 xe trở lên liên quan")
        triggered_rules.extend(_infer_description_complexity(incident.description))

        if triggered_rules:
            # Rõ ràng phức tạp → skip LLM hoàn toàn
            description = (
                f"Sự cố được phân loại PHỨC TẠP bởi rule-based engine. "
                f"Tiêu chí kích hoạt: {', '.join(triggered_rules)}. "
                f"Khuyến nghị: chuyển Assisted Mode."
            )
            return TriageOutput(
                is_complex=True,
                description=description,
                triggered_rules=triggered_rules,
            )

        # ── STEP 2: RAG query với metadata filter ─────────────────
        rag_query = (
            f"đánh giá mức độ phức tạp của sự cố bảo hiểm ô tô, "
            f"có người bị thương: {'có' if incident.injuries else 'không'}, "
            f"có bên thứ ba: {'có' if incident.third_party_involved else 'không'}, "
            f"xe còn chạy được: {'có' if incident.vehicle_drivable else 'không'}, "
            f"cao tốc: {'có' if getattr(incident, 'highway_incident', None) else 'không'}, "
            f"số xe liên quan: {incident.number_of_vehicles_involved or 'không rõ'}, "
            f"cần cứu hộ: {'có' if getattr(incident, 'towing_required', None) else 'không rõ'}, "
            f"sự cố: {incident.description}"
        )

        rag_where = _build_policy_filter(insurer=incident.insurer)
        rag_context, triage_citations = _retrieve_policy_context(
            query=rag_query,
            where=rag_where,
            k=agent_settings.TRIAGE_RAG_K,
        )

        # ── STEP 3: Cache RAG context cho Agent 2 ─────────────────
        self._rag_cache[session_id] = {
            "context": rag_context,
            "citations": triage_citations,
        }

        # ── STEP 4: LLM classify ─────────────────────────────────
        prompt = f"""Bạn là Agent phân loại sự cố bảo hiểm ô tô (Triage Agent).

## Thông tin sự cố từ người dùng:
- Thời gian: {incident.time}
- Địa điểm: {incident.location}
- GPS: {incident.gps_coordinates or "không rõ"}
- Mô tả sự cố: {incident.description}
- Loại sự cố: {incident.incident_type.value if incident.incident_type else "không rõ"}
- Có bên thứ ba liên quan: {"Có" if incident.third_party_involved else "Không"}
- Xe còn chạy được: {"Có" if incident.vehicle_drivable else "Không"}
- Có người bị thương: {"Có" if incident.injuries else "Không"}
- Xảy ra trên cao tốc: {"Có" if getattr(incident, 'highway_incident', None) else "Không"}
- Số xe liên quan: {incident.number_of_vehicles_involved or "Không rõ"}
- Thiệt hại ước tính: {incident.estimated_damage or "Không rõ"} VNĐ
- Điều kiện thời tiết: {incident.weather_condition or "Không rõ"}
- Điều kiện mặt đường: {incident.road_condition or "Không rõ"}
- Cần cứu hộ: {"Có" if getattr(incident, 'towing_required', None) else "Không rõ"}

## Điều khoản bảo hiểm tham khảo (từ RAG):
{rag_context}

## Tiêu chí phân loại "Phức tạp" (is_complex = true):
1. Có người bị thương hoặc tử vong
2. Có liên quan đến bên thứ ba (xe khác, người đi bộ, tài sản người khác)
3. Tai nạn liên hoàn (từ 3 xe trở lên)
4. Xảy ra trên đường cao tốc hoặc bối cảnh hiện trường cần giữ nguyên để phối hợp xử lý
5. Có dấu hiệu vụ việc phức tạp cần phối hợp công an / cứu hộ / insurer ngay

## Yêu cầu:
Phân tích kỹ thông tin sự cố, đối chiếu với điều khoản bảo hiểm, và trả về JSON:
{{
    "is_complex": true hoặc false,
    "description": "Giải thích chi tiết lý do phân loại, và nếu có dẫn chiếu thì dùng đúng citation đã có trong context theo format [source | article | chunk_id]."
}}

Chỉ trả về JSON, không thêm text nào khác."""

        try:
            raw_response = _call_llm(prompt)
            result = _parse_json_response(raw_response)
            return TriageOutput(
                is_complex=result.get("is_complex", True),
                description=result.get("description", "Không thể phân tích chi tiết."),
                triggered_rules=[],  # LLM classify, không phải rule-based
                citations=triage_citations,
            )
        except Exception as e:
            # Fallback: nếu LLM lỗi, mặc định là phức tạp (an toàn hơn)
            return TriageOutput(
                is_complex=True,
                description=(
                    f"[Fallback] Lỗi phân tích LLM: {str(e)}. "
                    f"Mặc định phân loại là phức tạp để đảm bảo an toàn."
                ),
                triggered_rules=["LLM Error → Fallback COMPLEX"],
                citations=triage_citations,
            )

    # ================================================================
    # AGENT 2: COVERAGE AGENT (Coverage Pre-check)
    # ================================================================
    def run_coverage_agent(
        self,
        incident: IncidentInput,
        session_id: str = None,
    ) -> CoverageOutput:
        """
        Agent 2: Kiểm tra điều kiện bồi thường sơ bộ.

        Chỉ chạy khi Agent 1 phân loại sự cố là KHÔNG phức tạp.

        Pipeline:
            1. Rule-based policy validity check:
               - policy_active=False → không đủ điều kiện sơ bộ
               - incident_time ngoài policy_start_date/policy_end_date → không đủ điều kiện sơ bộ
            2. Rule-based exclusion check:
               - alcohol_involved=True → loại trừ
               - driver_license_valid=False → loại trừ
               - vehicle_registration_valid=False → loại trừ
            3. Load cached RAG context từ Agent 1
            4. RAG query bổ sung: insurer-specific nếu có policy liên kết
            5. Merge 2 context → LLM evaluate eligibility

        Args:
            incident: IncidentInput chứa thông tin sự cố từ user.
            session_id: UUID từ Agent 1 để load cached RAG context.
                        None → query lại toàn bộ (không cache).

        Returns:
            CoverageOutput: Gồm is_eligible (bool), description (str),
                            coverage_summary (str).
        """
        insurer = incident.insurer or "chung"
        insurer_filter = _build_policy_filter(insurer=incident.insurer)

        # ── STEP 1: Policy validity pre-check ─────────────────────
        validity_result, validity_reason = _check_policy_validity(incident)
        if validity_result is False:
            validity_context, validity_citations = _retrieve_policy_context(
                query=(
                    f"hiệu lực hợp đồng bảo hiểm ô tô, thời hạn bảo hiểm, "
                    f"điều kiện có hiệu lực policy {insurer}, sự cố: {incident.description}"
                ),
                where=insurer_filter,
                k=agent_settings.COVERAGE_RAG_K,
            )
            return CoverageOutput(
                is_eligible=False,
                description=(
                    "Policy chưa đáp ứng điều kiện hiệu lực sơ bộ. "
                    f"{validity_reason}{_format_citation_tail(validity_citations)}"
                ),
                coverage_summary="Không đạt bước pre-check hiệu lực policy.",
                citations=validity_citations,
            )

        # ── STEP 2: Rule-based exclusion check (Điều 4) ───────────
        if getattr(incident, 'alcohol_involved', None):
            exclusion_context, exclusion_citations = _retrieve_policy_context(
                query=f"loại trừ bảo hiểm nồng độ cồn, insurer {insurer}, sự cố: {incident.description}",
                where=insurer_filter,
                k=agent_settings.COVERAGE_RAG_K,
            )
            return CoverageOutput(
                is_eligible=False,
                description=(
                    "Sự cố thuộc TRƯỜNG HỢP LOẠI TRỪ sơ bộ: "
                    "lái xe vi phạm nồng độ cồn. Bảo hiểm có nguy cơ KHÔNG chi trả."
                    f"{_format_citation_tail(exclusion_citations)}"
                ),
                coverage_summary=(
                    "Loại trừ sơ bộ: nồng độ cồn."
                    f"{_format_citation_tail(exclusion_citations, limit=2)}"
                ),
                citations=exclusion_citations,
            )

        if getattr(incident, 'driver_license_valid', None) is False:
            exclusion_context, exclusion_citations = _retrieve_policy_context(
                query=f"loại trừ bảo hiểm GPLX không hợp lệ, insurer {insurer}, sự cố: {incident.description}",
                where=insurer_filter,
                k=agent_settings.COVERAGE_RAG_K,
            )
            return CoverageOutput(
                is_eligible=False,
                description=(
                    "Sự cố thuộc TRƯỜNG HỢP LOẠI TRỪ sơ bộ: "
                    "GPLX không hợp lệ hoặc đã hết hạn. Bảo hiểm có nguy cơ KHÔNG chi trả."
                    f"{_format_citation_tail(exclusion_citations)}"
                ),
                coverage_summary=(
                    "Loại trừ sơ bộ: GPLX không hợp lệ."
                    f"{_format_citation_tail(exclusion_citations, limit=2)}"
                ),
                citations=exclusion_citations,
            )

        if getattr(incident, 'vehicle_registration_valid', None) is False:
            exclusion_context, exclusion_citations = _retrieve_policy_context(
                query=f"loại trừ bảo hiểm đăng kiểm hết hạn, insurer {insurer}, sự cố: {incident.description}",
                where=insurer_filter,
                k=agent_settings.COVERAGE_RAG_K,
            )
            return CoverageOutput(
                is_eligible=False,
                description=(
                    "Sự cố thuộc TRƯỜNG HỢP LOẠI TRỪ sơ bộ: "
                    "giấy đăng kiểm an toàn kỹ thuật đã hết hạn. Bảo hiểm có nguy cơ KHÔNG chi trả."
                    f"{_format_citation_tail(exclusion_citations)}"
                ),
                coverage_summary=(
                    "Loại trừ sơ bộ: đăng kiểm hết hạn."
                    f"{_format_citation_tail(exclusion_citations, limit=2)}"
                ),
                citations=exclusion_citations,
            )

        # ── STEP 3: Load cached RAG context từ Agent 1 ────────────
        cached_context = ""
        cached_citations = []
        if session_id and session_id in self._rag_cache:
            cached_payload = self._rag_cache.pop(session_id)  # Pop = dùng xong xóa
            if isinstance(cached_payload, dict):
                cached_context = cached_payload.get("context", "")
                cached_citations = cached_payload.get("citations", [])
            elif isinstance(cached_payload, str):
                cached_context = cached_payload

        # ── STEP 4: RAG query bổ sung (insurer-specific) ──────────
        rag_query = (
            f"coverage pre-check bảo hiểm ô tô {insurer}, "
            f"hiệu lực policy, phạm vi bảo hiểm, quyền lợi, loại trừ, miễn thường, "
            f"sự cố: {incident.description}"
        )
        new_context, new_citations = _retrieve_policy_context(
            query=rag_query,
            where=insurer_filter,
            k=agent_settings.COVERAGE_RAG_K,
        )

        # ── STEP 5: Merge context (cached + new) ─────────────────
        if cached_context and new_context:
            merged_context = f"{cached_context}\n\n===\n\n{new_context}"
        else:
            merged_context = new_context or cached_context or "[Không có context]"
        merged_citations = _dedupe_citations(cached_citations + new_citations)

        # ── STEP 6: LLM evaluate eligibility ─────────────────────
        prompt = f"""Bạn là Agent kiểm tra điều kiện bồi thường bảo hiểm ô tô (Coverage Agent).

## Thông tin sự cố:
- Mô tả: {incident.description}
- Loại sự cố: {incident.incident_type.value if incident.incident_type else "không rõ"}
- Thời gian: {incident.time}
- Địa điểm: {incident.location}
- GPS: {incident.gps_coordinates or "không rõ"}
- Nhà bảo hiểm: {insurer}
- Mã hợp đồng: {incident.policy_id or "Không rõ"}
- Policy active: {incident.policy_active if incident.policy_active is not None else "Không rõ"}
- Hiệu lực policy: {incident.policy_start_date or "Không rõ"} -> {incident.policy_end_date or "Không rõ"}
- GPLX hợp lệ: {"Không" if getattr(incident, 'driver_license_valid', None) is False else "Có/Không rõ"}
- Đăng kiểm hợp lệ: {"Không" if getattr(incident, 'vehicle_registration_valid', None) is False else "Có/Không rõ"}
- Nồng độ cồn: {"Không" if not getattr(incident, 'alcohol_involved', None) else "Có"}
- Bộ phận tổn thất: {', '.join(incident.damage_parts) if incident.damage_parts else "Không rõ"}
- Mức thiệt hại ước tính: {incident.estimated_damage or "Không rõ"} VNĐ
- Mất cắp dạng: {incident.theft_scope or "Không áp dụng/không rõ"}

## Điều khoản bảo hiểm tham khảo (từ RAG):
{merged_context}

## Nhiệm vụ:
1. Kiểm tra policy có hiệu lực sơ bộ tại thời điểm xảy ra sự cố không
2. Kiểm tra sự cố có nằm trong PHẠM VI BẢO HIỂM không
3. Kiểm tra sự cố có thuộc TRƯỜNG HỢP LOẠI TRỪ không
4. Xác định mức miễn thường / khấu trừ (nếu có)
5. Đánh giá sơ bộ khả năng được bồi thường

## Yêu cầu:
Trả về JSON:
{{
    "is_eligible": true (đủ điều kiện sơ bộ) hoặc false (không đủ/bị loại trừ),
    "description": "Giải thích chi tiết: phạm vi bảo hiểm áp dụng, có loại trừ nào không, và kết luận. Nếu dẫn chiếu thì dùng đúng citation đã có trong context theo format [source | article | chunk_id].",
    "coverage_summary": "Tóm tắt ngắn điều khoản áp dụng, có thể kèm citation ngắn nếu cần"
}}

Chỉ trả về JSON, không thêm text nào khác."""

        try:
            raw_response = _call_llm(prompt)
            result = _parse_json_response(raw_response)
            return CoverageOutput(
                is_eligible=result.get("is_eligible", False),
                description=result.get("description", "Không thể phân tích chi tiết."),
                coverage_summary=result.get("coverage_summary"),
                citations=merged_citations,
            )
        except Exception as e:
            return CoverageOutput(
                is_eligible=False,
                description=(
                    f"[Fallback] Lỗi phân tích LLM: {str(e)}. "
                    f"Không thể xác nhận điều kiện bồi thường."
                ),
                coverage_summary=None,
                citations=merged_citations,
            )

    def get_session_id_from_cache(self) -> str:
        """Trả về session_id mới nhất trong cache (nếu có), dùng cho testing."""
        if self._rag_cache:
            return list(self._rag_cache.keys())[-1]
        return ""


# Singleton instance — dùng chung cho toàn bộ application
insurance_agents = InsuranceAgents()
