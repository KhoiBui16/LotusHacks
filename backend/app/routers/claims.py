from datetime import datetime, timezone
import json
import re
from typing import Annotated

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.agent.agents.insurance_agents import _call_llm, _parse_json_response, insurance_agents
from app.agent.models.schemas import IncidentInput as AgentIncidentInput
from app.agent.models.schemas import IncidentType as AgentIncidentType
from app.db import get_db
from app.models.claim import ClaimInDB, ClaimListItem, ClaimTimelineItem
from app.models.claim_document import ClaimDocumentInDB
from app.models.user import UserInDB
from app.models.vehicle import VehicleInDB
from app.schemas.claims import (
    AttachDocumentRequest,
    ClaimAppealRequest,
    ClaimAppealResponse,
    ClaimAdviceActionRequest,
    ClaimAdviceActionResponse,
    ClaimChatBootstrapResponse,
    CoverageCheckResponse,
    ClaimCreateRequest,
    ClaimDocumentResponse,
    ClaimSubmitRequest,
    ClaimUpdateRequest,
    DossierResponse,
    EligibilityResponse,
    FirstNoticeRequest,
    FirstNoticeResponse,
    PolicyImportRequest,
    PolicyImportResponse,
    RequiredDoc,
    SubmitRouterRequest,
    SubmitRouterResponse,
    TriageResponse,
    ValidationResponse,
    ValidationResultItem,
)
from app.schemas.me import OkResponse
from app.security.deps import get_current_user

router = APIRouter(prefix="/claims", tags=["claims"])

_AGENT_INCIDENT_TYPE_MAP = {
    "collision": AgentIncidentType.COLLISION,
    "scratch": AgentIncidentType.SCRATCH,
    "glass": AgentIncidentType.GLASS_BREAK,
    "flood": AgentIncidentType.FLOOD,
    "theft": AgentIncidentType.THEFT,
    "other": AgentIncidentType.OTHER,
}
_GPS_COORDINATES_PATTERN = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")
_HIGHWAY_KEYWORDS = ("cao tốc", "cao toc", "highway", "expressway")
_MULTI_VEHICLE_PATTERN = re.compile(r"\b(\d+)\s*xe\b", re.IGNORECASE)


async def notify_admins_about_claim(
    db: AsyncIOMotorDatabase,
    *,
    claim_id: str,
    claim_short_id: str,
    creator_name: str,
    creator_email: str,
    message: str,
    now: datetime,
) -> None:
    admin_ids: list[ObjectId] = []
    async for admin in db["users"].find({"role": "admin"}, {"_id": 1}):
        admin_ids.append(admin["_id"])
    if not admin_ids:
        return

    docs = [
        {
            "user_id": admin_id,
            "type": "info",
            "title": f"New claim update: {claim_short_id}",
            "message": f"{creator_name} ({creator_email}) {message}",
            "claim_id": ObjectId(claim_id),
            "read": False,
            "created_at": now,
        }
        for admin_id in admin_ids
    ]
    await db["notifications"].insert_many(docs)


def required_docs(*, police_report_required: bool) -> list[RequiredDoc]:
    return [
        RequiredDoc(
            doc_type="vehicle-overall",
            title="Vehicle overall",
            mime_allowed=["image/jpeg", "image/png"],
            max_size_mb=20,
        ),
        RequiredDoc(
            doc_type="damage-closeup",
            title="Damage close-up",
            mime_allowed=["image/jpeg", "image/png"],
            max_size_mb=20,
        ),
        RequiredDoc(
            doc_type="scene",
            title="Scene photo",
            mime_allowed=["image/jpeg", "image/png"],
            max_size_mb=20,
        ),
        RequiredDoc(
            doc_type="insurance-cert",
            title="Insurance certificate",
            mime_allowed=["image/jpeg", "image/png", "application/pdf"],
            max_size_mb=20,
        ),
        RequiredDoc(
            doc_type="police-report",
            title="Police report",
            mime_allowed=["image/jpeg", "image/png", "application/pdf"],
            max_size_mb=20,
            required=police_report_required,
        ),
    ]


def _build_incident_timestamp(date_value: str, time_value: str | None) -> str:
    """Ghép date + time từ claim hiện tại về format agent đang dùng."""
    return f"{date_value} {time_value}".strip() if time_value else date_value


def _extract_gps_coordinates(location_text: str) -> str | None:
    """Nếu user đang lưu `lat,lng` ở step location thì chuyển sang GPS field riêng."""
    return location_text if _GPS_COORDINATES_PATTERN.match(location_text or "") else None


def _infer_highway_incident(location_text: str, description: str | None) -> bool:
    """Suy ra tín hiệu cao tốc từ location/description hiện có của BE."""
    haystack = f"{location_text} {description or ''}".lower()
    return any(keyword in haystack for keyword in _HIGHWAY_KEYWORDS)


def _infer_number_of_vehicles(description: str | None, has_third_party: bool) -> int:
    """
    Suy luận số xe liên quan từ mô tả tự do.

    Main hiện chưa thu riêng field này, nên adapter chỉ lấy từ text nếu có;
    fallback tối thiểu là 2 xe khi có bên thứ ba, hoặc 1 xe nếu không.
    """
    description_text = description or ""
    match = _MULTI_VEHICLE_PATTERN.search(description_text)
    if match:
        try:
            return max(int(match.group(1)), 1)
        except ValueError:
            pass

    lowered = description_text.lower()
    if "liên hoàn" in lowered:
        return 3
    if has_third_party:
        return 2
    return 1


def _to_agent_incident_type(raw_type: str | None) -> AgentIncidentType:
    """Map incident type của claim hiện tại sang enum của workflow agent."""
    return _AGENT_INCIDENT_TYPE_MAP.get(raw_type or "", AgentIncidentType.OTHER)


def _claim_has_linked_policy(claim: ClaimInDB, vehicle: VehicleInDB | None) -> bool:
    """Xác định xem claim hiện có policy linked hay chưa."""
    return bool(
        claim.policy_id
        or claim.insurer
        or (vehicle and (vehicle.policy_linked or vehicle.policy_id or vehicle.insurer))
    )


async def _load_claim_vehicle(
    db: AsyncIOMotorDatabase,
    *,
    claim: ClaimInDB,
    user_id: str,
) -> VehicleInDB | None:
    """Lấy vehicle linked để agent đọc insurer/policy validity thật từ main."""
    vehicle_doc = await db["vehicles"].find_one(
        {"_id": ObjectId(claim.vehicle_id), "user_id": ObjectId(user_id)}
    )
    if not vehicle_doc:
        return None
    return VehicleInDB.from_mongo(vehicle_doc)


def _build_agent_incident_input(
    *,
    claim: ClaimInDB,
    vehicle: VehicleInDB | None,
) -> AgentIncidentInput:
    """
    Chuyển dữ liệu claim/vehicle hiện có của main sang schema input của workflow agent.

    Đây là adapter trung tâm để workflow agent dùng đúng dữ liệu thật từ 7 bước
    thay cho dummy payload.
    """
    incident = claim.incident
    if not incident:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incident intake is incomplete")

    location_text = incident.location_text.strip()
    gps_coordinates = _extract_gps_coordinates(location_text)
    insurer = claim.insurer or (vehicle.insurer if vehicle else None)
    policy_id = claim.policy_id or (vehicle.policy_id if vehicle else None)
    policy_linked = _claim_has_linked_policy(claim, vehicle)

    return AgentIncidentInput(
        time=_build_incident_timestamp(incident.date, incident.time),
        location=location_text,
        gps_coordinates=gps_coordinates,
        description=incident.description or f"Incident reported as {incident.type}.",
        incident_type=_to_agent_incident_type(incident.type),
        third_party_involved=incident.has_third_party,
        vehicle_drivable=incident.can_drive,
        injuries=incident.has_injury,
        policy_id=policy_id,
        insurer=insurer,
        policy_active=True if policy_linked else False,
        policy_start_date=vehicle.effective_date if vehicle else None,
        policy_end_date=vehicle.expiry if vehicle else None,
        vehicle_plate=vehicle.plate if vehicle else None,
        vehicle_model=vehicle.model if vehicle else None,
        highway_incident=_infer_highway_incident(location_text, incident.description),
        number_of_vehicles_involved=_infer_number_of_vehicles(incident.description, incident.has_third_party),
        towing_required=incident.needs_towing,
        police_report=incident.has_injury or incident.has_third_party,
        notes=incident.third_party_info,
    )


def _triage_risk_level(agent_incident: AgentIncidentInput, assisted_mode: bool) -> str:
    """Suy ra risk level theo contract hiện có của main."""
    if assisted_mode:
        return "high"
    if agent_incident.towing_required or agent_incident.incident_type in {
        AgentIncidentType.FLOOD,
        AgentIncidentType.THEFT,
    }:
        return "medium"
    return "low"


def _build_coverage_check(
    *,
    claim: ClaimInDB,
    vehicle: VehicleInDB | None,
    is_eligible: bool,
    coverage_summary: str | None,
    description: str,
) -> CoverageCheckResponse:
    """Map kết quả Agent 2 về shape eligibility hiện tại của main."""
    has_policy = _claim_has_linked_policy(claim, vehicle)
    description_lower = description.lower()
    policy_active = has_policy and not ((not is_eligible) and "hiệu lực" in description_lower)
    likely_excluded = (not is_eligible) and "hiệu lực" not in description_lower
    return CoverageCheckResponse(
        policy_active=policy_active,
        has_policy=has_policy,
        likely_excluded=likely_excluded,
        deductible_notice=coverage_summary,
    )


def _serialize_policy_citations(citations: list) -> list[dict]:
    return [citation.model_dump() for citation in (citations or [])]


def _build_incident_snapshot(
    *,
    claim: ClaimInDB,
    agent_incident: AgentIncidentInput,
) -> dict:
    incident = claim.incident
    if not incident:
        return {}

    return {
        "claim_id": claim.id,
        "incident_type": incident.type,
        "date": incident.date,
        "time": incident.time,
        "location_text": incident.location_text,
        "description": incident.description,
        "has_third_party": incident.has_third_party,
        "third_party_info": incident.third_party_info,
        "can_drive": incident.can_drive,
        "needs_towing": incident.needs_towing,
        "has_injury": incident.has_injury,
        "agent_input": agent_incident.model_dump(mode="json"),
    }


def _build_policy_snapshot(
    *,
    claim: ClaimInDB,
    vehicle: VehicleInDB | None,
) -> dict:
    return {
        "claim_policy_id": claim.policy_id,
        "claim_insurer": claim.insurer,
        "vehicle_policy_linked": vehicle.policy_linked if vehicle else False,
        "vehicle_policy_id": vehicle.policy_id if vehicle else None,
        "vehicle_insurer": vehicle.insurer if vehicle else None,
        "policy_effective_date": vehicle.effective_date if vehicle else None,
        "policy_expiry": vehicle.expiry if vehicle else None,
        "additional_benefits": list(vehicle.additional_benefits) if vehicle else [],
        "vehicle_plate": vehicle.plate if vehicle else None,
        "vehicle_model": vehicle.model if vehicle else None,
    }


async def _build_required_doc_profile(
    db: AsyncIOMotorDatabase,
    *,
    claim: ClaimInDB,
) -> list[dict]:
    await ensure_required_doc_stubs(db, claim)
    docs = await db["claim_documents"].find({"claim_id": ObjectId(claim.id)}).to_list(length=200)
    docs_by_type = {doc["doc_type"]: doc for doc in docs}

    profile = []
    for required_doc in required_docs_for_claim(claim):
        existing = docs_by_type.get(required_doc.doc_type, {})
        profile.append(
            {
                "doc_type": required_doc.doc_type,
                "title": required_doc.title,
                "required": required_doc.required,
                "status": existing.get("status", "missing"),
                "note": existing.get("note"),
                "upload_id": existing.get("upload_id"),
            }
        )
    return profile


def _build_chat_title(*, claim: ClaimInDB, vehicle: VehicleInDB | None) -> str:
    incident_type = (claim.incident.type if claim.incident else "claim").replace("-", " ").title()
    plate = vehicle.plate if vehicle and vehicle.plate else "vehicle"
    return f"{incident_type} guidance - {plate}"


def _build_chat_context_seed(
    *,
    claim: ClaimInDB,
    vehicle: VehicleInDB | None,
    triage_doc: dict,
    eligibility_result: EligibilityResponse,
    required_doc_profile: list[dict],
) -> str:
    incident = claim.incident
    if not incident:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incident intake is incomplete")

    required_lines = "\n".join(
        f"- {doc['title']} ({doc['doc_type']}): required={doc['required']}, status={doc['status']}"
        for doc in required_doc_profile
    ) or "- No document profile available."

    notes = "\n".join(f"- {note}" for note in eligibility_result.notes) or "- No pre-check notes."
    triage_reasons = "\n".join(f"- {reason}" for reason in triage_doc.get("reasons", [])) or "- No triage reasons."

    return (
        "You are the claim preparation assistant for an auto insurance claim in Vietnam.\n"
        "Stay grounded in the current claim context below. Do not restart triage. "
        "Treat coverage as a preliminary pre-check only, not a final approval.\n\n"
        f"Claim ID: {claim.id}\n"
        f"Vehicle: {(vehicle.model if vehicle else 'Unknown vehicle')} / {(vehicle.plate if vehicle else 'No plate')}\n"
        f"Incident type: {incident.type}\n"
        f"Incident date: {incident.date}\n"
        f"Incident time: {incident.time or 'Not provided'}\n"
        f"Location: {incident.location_text}\n"
        f"Description: {incident.description or 'No additional description'}\n"
        f"Third party involved: {incident.has_third_party}\n"
        f"Vehicle can drive: {incident.can_drive}\n"
        f"Needs towing: {incident.needs_towing}\n"
        f"Injury reported: {incident.has_injury}\n\n"
        f"Triage reasons:\n{triage_reasons}\n\n"
        f"Eligibility outcome: {eligibility_result.outcome}\n"
        f"Next action: {eligibility_result.next_action}\n"
        f"Coverage notes:\n{notes}\n\n"
        f"Required document profile:\n{required_lines}\n\n"
        "Your job in this chat is to guide the user through claim preparation, explain the current checklist, "
        "and help them understand what evidence or documents they should prepare next."
    )


def _fallback_claim_advice(
    *,
    coverage: CoverageCheckResponse,
    coverage_notes: list[str],
    required_doc_profile: list[dict],
) -> tuple[str, list[str]]:
    missing_required = [doc["title"] for doc in required_doc_profile if doc["required"] and doc["status"] == "missing"]

    if not coverage.has_policy:
        advice_text = (
            "Chưa có đủ thông tin policy liên kết để tiếp tục claim một cách chắc chắn. "
            "Nếu bạn chưa import hợp đồng hoặc giấy chứng nhận bảo hiểm, nên lưu draft và bổ sung trước."
        )
        actions = [
            "Lưu draft hồ sơ để bổ sung policy hoặc giấy chứng nhận bảo hiểm.",
            "Chỉ cân nhắc claim lại sau khi đã xác minh insurer, số hợp đồng và thời hạn hiệu lực.",
            "Nếu thiệt hại nhỏ, có thể cân nhắc tự sửa ngoài để tiết kiệm thời gian.",
        ]
    elif not coverage.policy_active:
        advice_text = (
            "Kết quả pre-check cho thấy policy hiện tại có thể không còn hiệu lực tại thời điểm sự cố, "
            "nên khả năng tiếp tục claim đang thấp."
        )
        actions = [
            "Rà soát lại ngày hiệu lực và ngày hết hạn của policy trước khi claim lại.",
            "Lưu draft để giữ lại thông tin sự cố và chứng cứ ban đầu.",
            "Nếu chi phí khắc phục thấp, có thể cân nhắc tự sửa ngoài thay vì mở claim ngay.",
        ]
    elif coverage.likely_excluded:
        advice_text = (
            "Tình huống hiện tại có dấu hiệu rơi vào trường hợp bị loại trừ hoặc chưa đủ lợi thế để tiếp tục claim sơ bộ."
        )
        actions = [
            "Xem lại quyền lợi bổ sung và điều khoản loại trừ của policy trước khi quyết định claim.",
            "Nếu mức tổn thất nhỏ, cân nhắc tự sửa ngoài thay vì nộp claim ngay.",
            "Lưu draft để có thể tiếp tục sau khi bổ sung thêm giấy tờ hoặc thông tin còn thiếu.",
        ]
    else:
        advice_text = (
            "Kết quả pre-check hiện chưa ủng hộ việc tiếp tục claim ngay. "
            "Bạn nên giữ lại hồ sơ ở dạng draft và chỉ mở claim lại khi có thêm căn cứ rõ hơn."
        )
        actions = [
            "Lưu draft để giữ lại thông tin sự cố và các tài liệu đã có.",
            "Bổ sung thêm policy, chứng từ hoặc bằng chứng hiện trường nếu có.",
            "Nếu thiệt hại nhỏ, cân nhắc phương án tự sửa ngoài.",
        ]

    if missing_required:
        actions.append(f"Bổ sung các giấy tờ còn thiếu như: {', '.join(missing_required[:3])}.")

    if coverage_notes:
        actions.append(f"Ghi nhớ kết luận sơ bộ hiện tại: {coverage_notes[0]}")

    deduped_actions = []
    for action in actions:
        if action not in deduped_actions:
            deduped_actions.append(action)

    return advice_text, deduped_actions[:4]


async def _generate_claim_advice(
    *,
    incident_snapshot: dict,
    policy_snapshot: dict,
    coverage: CoverageCheckResponse,
    eligibility_notes: list[str],
    required_doc_profile: list[dict],
) -> dict:
    fallback_text, fallback_actions = _fallback_claim_advice(
        coverage=coverage,
        coverage_notes=eligibility_notes,
        required_doc_profile=required_doc_profile,
    )

    prompt = (
        "Dua tren du lieu pre-check bao hiem o to duoi day, hay tao loi khuyen ngan gon cho user.\n"
        "Bat buoc tra ve JSON hop le voi schema:\n"
        "{\n"
        '  "advice_text": "string",\n'
        '  "recommended_actions": ["string"],\n'
        '  "should_claim": false,\n'
        '  "save_option_available": true,\n'
        '  "end_flow_available": true\n'
        "}\n"
        "Quy tac:\n"
        "- Giu giong dieu huong thuc te, khong qua phap ly.\n"
        "- Khong duoc noi rang claim chac chan duoc duyet.\n"
        "- Tap trung vao 2-4 hanh dong tiep theo.\n"
        "- Neu thieu policy hoac nghi het hieu luc, nen uu tien luu draft va bo sung.\n"
        "- Van phai giu should_claim=false.\n\n"
        f"incident_snapshot={json.dumps(incident_snapshot, ensure_ascii=False)}\n"
        f"policy_snapshot={json.dumps(policy_snapshot, ensure_ascii=False)}\n"
        f"coverage={json.dumps(coverage.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"eligibility_notes={json.dumps(eligibility_notes, ensure_ascii=False)}\n"
        f"required_doc_profile={json.dumps(required_doc_profile, ensure_ascii=False)}\n"
    )

    try:
        content = _call_llm(prompt)
        parsed = _parse_json_response(content)
        advice_text = str(parsed.get("advice_text") or "").strip()
        raw_actions = parsed.get("recommended_actions") or []
        recommended_actions = [
            str(item).strip()
            for item in raw_actions
            if isinstance(item, str) and str(item).strip()
        ]
        if not advice_text:
            raise ValueError("Advice text is empty")
        if not recommended_actions:
            recommended_actions = fallback_actions
        return {
            "advice_text": advice_text,
            "recommended_actions": recommended_actions[:4],
            "should_claim": False,
            "save_option_available": True,
            "end_flow_available": True,
            "generation_mode": "llm_advice",
        }
    except Exception:
        return {
            "advice_text": fallback_text,
            "recommended_actions": fallback_actions,
            "should_claim": False,
            "save_option_available": True,
            "end_flow_available": True,
            "generation_mode": "fallback_rule_advice",
        }


async def _persist_triage_result(
    db: AsyncIOMotorDatabase,
    *,
    claim_id: str,
    user_id: str,
    claim: ClaimInDB,
    agent_incident: AgentIncidentInput,
    triage_result,
    now: datetime,
) -> dict:
    assisted = triage_result.is_complex
    reasons = triage_result.triggered_rules or [triage_result.description]
    risk_level = _triage_risk_level(agent_incident, assisted)
    incident_snapshot = _build_incident_snapshot(claim=claim, agent_incident=agent_incident)

    triage_doc = {
        "risk_level": risk_level,
        "assisted_mode": assisted,
        "reasons": reasons,
        "description": triage_result.description,
        "citations": _serialize_policy_citations(triage_result.citations),
        "source": "agent_workflow",
        "at": now,
    }
    triage_internal = {
        "input_snapshot": incident_snapshot,
        "rule_hits": triage_result.triggered_rules,
        "rule_version": "current_agent_rules",
        "decision": "yes" if assisted else "no",
        "description": triage_result.description,
        "citations": _serialize_policy_citations(triage_result.citations),
        "source_mode": "agent_workflow",
        "generated_at": now,
    }

    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user_id)},
        {"$set": {"triage": triage_doc, "triage_internal": triage_internal, "updated_at": now}},
    )
    return triage_doc


def _update_timeline_with_label(claim: ClaimInDB, *, label: str, at: datetime) -> list[dict]:
    timeline = [ClaimTimelineItem.model_validate(item).model_dump() for item in claim.timeline]
    for item in timeline:
        if item.get("status") == "current":
            item["status"] = "done"
    timeline.append({"at": at, "label": label, "status": "current"})
    return timeline


def required_docs_for_claim(claim: ClaimInDB) -> list[RequiredDoc]:
    police_required = False
    if claim.incident and (claim.incident.has_injury or claim.incident.has_third_party):
        police_required = True
    return required_docs(police_report_required=police_required)


async def ensure_required_doc_stubs(db: AsyncIOMotorDatabase, claim: ClaimInDB) -> None:
    now = datetime.now(timezone.utc)
    for d in required_docs_for_claim(claim):
        await db["claim_documents"].update_one(
            {"claim_id": ObjectId(claim.id), "doc_type": d.doc_type},
            {
                "$setOnInsert": {
                    "required": d.required,
                    "status": "missing",
                    "note": None,
                    "upload_id": None,
                    "url": None,
                    "created_at": now,
                },
                "$set": {"updated_at": now},
            },
            upsert=True,
        )


@router.get("", response_model=list[ClaimListItem])
async def list_claims(
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    status_filter: str | None = Query(default=None, alias="status"),
    vehicle_id: str | None = Query(default=None, alias="vehicle_id"),
    q: str | None = Query(default=None, alias="q"),
) -> list[ClaimListItem]:
    query: dict = {"user_id": ObjectId(user.id)}
    if status_filter:
        query["status"] = status_filter
    if vehicle_id:
        query["vehicle_id"] = ObjectId(vehicle_id)

    cursor = db["claims"].find(query).sort("updated_at", -1)
    vehicles = db["vehicles"]
    items: list[ClaimListItem] = []
    async for doc in cursor:
        c = ClaimInDB.from_mongo(doc)
        v = await vehicles.find_one({"_id": ObjectId(c.vehicle_id), "user_id": ObjectId(user.id)})
        plate = v.get("plate") if v else None
        claim_type = c.incident.type if c.incident else "claim"
        claim_date = c.incident.date if c.incident else c.created_at.date().isoformat()
        item = ClaimListItem(
            id=c.id,
            type=str(claim_type),
            date=str(claim_date),
            vehicle_plate=plate,
            vehicle_id=c.vehicle_id,
            insurer=c.insurer,
            status=c.status,
            amount_value=c.amount_value,
            amount_currency=c.amount_currency,
            updated_at=c.updated_at,
        )
        if q:
            hay = f"{item.type} {item.date} {item.vehicle_plate or ''} {item.insurer or ''}".lower()
            if q.lower() not in hay:
                continue
        items.append(item)
    return items


@router.post("", response_model=ClaimInDB, status_code=status.HTTP_201_CREATED)
async def create_claim(
    payload: ClaimCreateRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimInDB:
    if user.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Claim creation is disabled for admin accounts")

    vehicle = await db["vehicles"].find_one({"_id": ObjectId(payload.vehicle_id), "user_id": ObjectId(user.id)})
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": ObjectId(user.id),
        "vehicle_id": ObjectId(payload.vehicle_id),
        "insurer": payload.insurer,
        "policy_id": payload.policy_id,
        "status": "draft",
        "amount_value": None,
        "amount_currency": None,
        "incident": None,
        "timeline": [
            {"at": now, "label": "Draft created", "status": "current"},
        ],
        "created_at": now,
        "updated_at": now,
        "submitted_at": None,
    }
    result = await db["claims"].insert_one(doc)
    saved = await db["claims"].find_one({"_id": result.inserted_id})
    if not saved:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create claim")
    claim = ClaimInDB.from_mongo(saved)
    await ensure_required_doc_stubs(db, claim)
    await notify_admins_about_claim(
        db,
        claim_id=claim.id,
        claim_short_id=claim.id[-8:],
        creator_name=user.full_name,
        creator_email=user.email,
        message="created a new claim draft.",
        now=now,
    )
    return claim


@router.get("/{claim_id}", response_model=ClaimInDB)
async def get_claim(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimInDB:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    claim = ClaimInDB.from_mongo(doc)
    await ensure_required_doc_stubs(db, claim)
    return claim


@router.patch("/{claim_id}", response_model=ClaimInDB)
async def update_claim(
    claim_id: str,
    payload: ClaimUpdateRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimInDB:
    try:
        claim_obj_id = ObjectId(claim_id)
        user_obj_id = ObjectId(user.id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim id")

    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc)
        res = await db["claims"].update_one(
            {"_id": claim_obj_id, "user_id": user_obj_id},
            {"$set": updates},
        )
        if res.matched_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    doc = await db["claims"].find_one({"_id": claim_obj_id, "user_id": user_obj_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return ClaimInDB.from_mongo(doc)


@router.post("/{claim_id}/submit", response_model=ClaimInDB)
async def submit_claim(
    claim_id: str,
    payload: ClaimSubmitRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimInDB:
    if not payload.consent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Consent required")

    now = datetime.now(timezone.utc)
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim = ClaimInDB.from_mongo(doc)
    timeline = [ClaimTimelineItem.model_validate(i).model_dump() for i in claim.timeline]
    for i in timeline:
        if i.get("status") == "current":
            i["status"] = "done"
    timeline.append({"at": now, "label": "Submitted", "status": "current"})

    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {
            "$set": {
                "status": "processing",
                "submitted_at": now,
                "timeline": timeline,
                "updated_at": now,
            }
        },
    )

    await db["notifications"].insert_one(
        {
            "user_id": ObjectId(user.id),
            "type": "status",
            "title": "Claim submitted",
            "message": "Your claim has been submitted and is now being processed.",
            "claim_id": ObjectId(claim_id),
            "read": False,
            "created_at": now,
        }
    )
    await notify_admins_about_claim(
        db,
        claim_id=claim_id,
        claim_short_id=claim_id[-8:],
        creator_name=user.full_name,
        creator_email=user.email,
        message="submitted a claim for processing.",
        now=now,
    )

    updated = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return ClaimInDB.from_mongo(updated)


@router.get("/{claim_id}/timeline", response_model=list[ClaimTimelineItem])
async def get_claim_timeline(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> list[ClaimTimelineItem]:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)}, {"timeline": 1})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return [ClaimTimelineItem.model_validate(i) for i in doc.get("timeline", [])]


@router.get("/{claim_id}/required-docs", response_model=list[RequiredDoc])
async def get_required_docs(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> list[RequiredDoc]:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    claim = ClaimInDB.from_mongo(doc)
    return required_docs_for_claim(claim)


@router.get("/{claim_id}/documents", response_model=list[ClaimDocumentResponse])
async def list_documents(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> list[ClaimDocumentResponse]:
    claim = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)}, {"_id": 1})
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim_full_doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not claim_full_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    claim_obj = ClaimInDB.from_mongo(claim_full_doc)
    await ensure_required_doc_stubs(db, claim_obj)
    cursor = db["claim_documents"].find({"claim_id": ObjectId(claim_id)}).sort("doc_type", 1)
    out: list[ClaimDocumentResponse] = []
    async for doc in cursor:
        d = ClaimDocumentInDB.from_mongo(doc)
        out.append(
            ClaimDocumentResponse(
                id=d.id,
                claim_id=d.claim_id,
                doc_type=d.doc_type,
                required=d.required,
                status=d.status,
                note=d.note,
                upload_id=d.upload_id,
                url=d.url,
            )
        )
    return out


@router.post("/{claim_id}/documents", response_model=ClaimDocumentResponse)
async def attach_document(
    claim_id: str,
    payload: AttachDocumentRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimDocumentResponse:
    claim = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)}, {"_id": 1})
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    upload = await db["uploads"].find_one({"_id": ObjectId(payload.upload_id), "user_id": ObjectId(user.id)})
    if not upload:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")

    now = datetime.now(timezone.utc)
    await db["claim_documents"].update_one(
        {"claim_id": ObjectId(claim_id), "doc_type": payload.doc_type},
        {
            "$set": {
                "upload_id": payload.upload_id,
                "url": upload.get("url"),
                "status": "uploaded",
                "updated_at": now,
            },
            "$setOnInsert": {"required": True, "created_at": now, "note": None},
        },
        upsert=True,
    )
    doc = await db["claim_documents"].find_one({"claim_id": ObjectId(claim_id), "doc_type": payload.doc_type})
    if not doc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to attach document")
    d = ClaimDocumentInDB.from_mongo(doc)
    return ClaimDocumentResponse(
        id=d.id,
        claim_id=d.claim_id,
        doc_type=d.doc_type,
        required=d.required,
        status=d.status,
        note=d.note,
        upload_id=d.upload_id,
        url=d.url,
    )


@router.post("/{claim_id}/validate", response_model=ValidationResponse)
async def validate_claim_documents(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ValidationResponse:
    claim = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)}, {"_id": 1})
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim_doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not claim_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    claim_obj = ClaimInDB.from_mongo(claim_doc)
    await ensure_required_doc_stubs(db, claim_obj)
    docs_map = {}
    async for doc in db["claim_documents"].find({"claim_id": ObjectId(claim_id)}):
        d = ClaimDocumentInDB.from_mongo(doc)
        docs_map[d.doc_type] = d

    now = datetime.now(timezone.utc)
    results: list[ValidationResultItem] = []
    overall = "ok"
    for req in required_docs_for_claim(claim_obj):
        d = docs_map.get(req.doc_type)
        if not req.required:
            results.append(ValidationResultItem(doc_type=req.doc_type, status="valid", note="Optional"))
            await db["claim_documents"].update_one(
                {"claim_id": ObjectId(claim_id), "doc_type": req.doc_type},
                {"$set": {"status": "valid", "note": "Optional", "updated_at": now}},
            )
            continue
        if d and d.upload_id:
            results.append(ValidationResultItem(doc_type=req.doc_type, status="valid", note="OK"))
            await db["claim_documents"].update_one(
                {"_id": ObjectId(d.id)},
                {"$set": {"status": "valid", "note": "OK", "updated_at": now}},
            )
        else:
            overall = "issues"
            results.append(ValidationResultItem(doc_type=req.doc_type, status="missing", note="Missing"))
            await db["claim_documents"].update_one(
                {"claim_id": ObjectId(claim_id), "doc_type": req.doc_type},
                {"$set": {"status": "missing", "note": "Missing", "updated_at": now}},
            )

    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {"$set": {"updated_at": now}},
    )
    return ValidationResponse(overall=overall, results=results)


@router.post("/{claim_id}/policy-import", response_model=PolicyImportResponse)
async def import_policy_for_claim(
    claim_id: str,
    payload: PolicyImportRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> PolicyImportResponse:
    try:
        claim_oid = ObjectId(claim_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim id")

    claim = await db["claims"].find_one({"_id": claim_oid, "user_id": ObjectId(user.id)})
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    now = datetime.now(timezone.utc)
    await db["claims"].update_one(
        {"_id": claim_oid, "user_id": ObjectId(user.id)},
        {
            "$set": {
                "policy_id": payload.policy_id,
                "insurer": payload.insurer,
                "policy_import": {
                    "source": payload.source,
                    "effective_date": payload.effective_date,
                    "expiry": payload.expiry,
                    "updated_at": now,
                },
                "updated_at": now,
            }
        },
    )

    await db["vehicles"].update_one(
        {"_id": claim.get("vehicle_id"), "user_id": ObjectId(user.id)},
        {
            "$set": {
                "policy_linked": True,
                "policy_id": payload.policy_id,
                "insurer": payload.insurer,
                "effective_date": payload.effective_date,
                "expiry": payload.expiry,
                "updated_at": now,
            }
        },
    )

    return PolicyImportResponse(
        claim_id=claim_id,
        policy_linked=True,
        policy_id=payload.policy_id,
        insurer=payload.insurer,
        source=payload.source,
    )


@router.post("/{claim_id}/triage", response_model=TriageResponse)
async def triage_claim(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> TriageResponse:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim = ClaimInDB.from_mongo(doc)
    vehicle = await _load_claim_vehicle(db, claim=claim, user_id=user.id)
    agent_incident = _build_agent_incident_input(claim=claim, vehicle=vehicle)

    try:
        triage_result = insurance_agents.run_triage_agent(agent_incident)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow triage failed: {exc}",
        )

    assisted = triage_result.is_complex
    reasons = triage_result.triggered_rules or [triage_result.description]
    risk_level = _triage_risk_level(agent_incident, assisted)

    now = datetime.now(timezone.utc)
    await _persist_triage_result(
        db,
        claim_id=claim_id,
        user_id=user.id,
        claim=claim,
        agent_incident=agent_incident,
        triage_result=triage_result,
        now=now,
    )

    return TriageResponse(claim_id=claim_id, risk_level=risk_level, assisted_mode=assisted, reasons=reasons)


@router.get("/{claim_id}/eligibility", response_model=EligibilityResponse)
async def get_eligibility(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> EligibilityResponse:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim = ClaimInDB.from_mongo(doc)
    vehicle = await _load_claim_vehicle(db, claim=claim, user_id=user.id)
    agent_incident = _build_agent_incident_input(claim=claim, vehicle=vehicle)

    triage_doc = doc.get("triage") or {}
    assisted_mode = triage_doc.get("assisted_mode")
    if assisted_mode is None:
        try:
            triage_result = insurance_agents.run_triage_agent(agent_incident)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Workflow triage failed: {exc}",
            )
        now = datetime.now(timezone.utc)
        triage_doc = await _persist_triage_result(
            db,
            claim_id=claim_id,
            user_id=user.id,
            claim=claim,
            agent_incident=agent_incident,
            triage_result=triage_result,
            now=now,
        )
        assisted_mode = triage_doc["assisted_mode"]

    incident_snapshot = _build_incident_snapshot(claim=claim, agent_incident=agent_incident)
    policy_snapshot = _build_policy_snapshot(claim=claim, vehicle=vehicle)
    required_doc_profile = await _build_required_doc_profile(db, claim=claim)

    if assisted_mode:
        result = EligibilityResponse(
            claim_id=claim_id,
            outcome="assisted_required",
            coverage=_build_coverage_check(
                claim=claim,
                vehicle=vehicle,
                is_eligible=True,
                coverage_summary="Coverage pre-check is deferred to Assisted Mode.",
                description="Complex case requires assisted handling before coverage pre-check.",
            ),
            next_action="assisted",
            notes=["Complex case requires assisted handling before coverage pre-check."],
        )
        coverage_precheck_internal = {
            "incident_snapshot": incident_snapshot,
            "triage_ref": {
                "assisted_mode": True,
                "reasons": triage_doc.get("reasons", []),
            },
            "policy_snapshot": policy_snapshot,
            "retrieval_mode": "deferred",
            "retrieval_status": "skipped_due_to_assisted_mode",
            "retrieved_chunks": [],
            "coverage_basis": "Coverage pre-check deferred to Assisted Mode.",
            "validity_checks": {"has_policy": result.coverage.has_policy},
            "exclusion_hits": [],
            "deductible_hint": result.coverage.deductible_notice,
            "required_doc_profile": required_doc_profile,
            "decision": "deferred",
            "description": "Complex case requires assisted handling before coverage pre-check.",
            "generated_at": datetime.now(timezone.utc),
        }
        advice_internal = None
    else:
        try:
            coverage_result = insurance_agents.run_coverage_agent(agent_incident)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Workflow eligibility failed: {exc}",
            )

        coverage = _build_coverage_check(
            claim=claim,
            vehicle=vehicle,
            is_eligible=coverage_result.is_eligible,
            coverage_summary=coverage_result.coverage_summary,
            description=coverage_result.description,
        )
        result = EligibilityResponse(
            claim_id=claim_id,
            outcome="likely_covered" if coverage_result.is_eligible else "low_value_or_excluded",
            coverage=coverage,
            next_action="chat" if coverage_result.is_eligible else "exit",
            notes=[coverage_result.description],
        )
        coverage_precheck_internal = {
            "incident_snapshot": incident_snapshot,
            "triage_ref": {
                "assisted_mode": False,
                "reasons": triage_doc.get("reasons", []),
            },
            "policy_snapshot": policy_snapshot,
            "retrieval_mode": "rule_plus_rag" if coverage_result.citations else "rule_only",
            "retrieval_status": "ok" if coverage_result.citations else "no_policy_citations",
            "retrieved_chunks": _serialize_policy_citations(coverage_result.citations),
            "coverage_basis": coverage_result.coverage_summary,
            "validity_checks": {
                "has_policy": coverage.has_policy,
                "policy_active": coverage.policy_active,
            },
            "exclusion_hits": ["likely_excluded"] if coverage.likely_excluded else [],
            "deductible_hint": coverage_result.coverage_summary,
            "required_doc_profile": required_doc_profile,
            "decision": "yes" if coverage_result.is_eligible else "no",
            "description": coverage_result.description,
            "generated_at": datetime.now(timezone.utc),
        }

        advice_internal = None
        if not coverage_result.is_eligible:
            advice_payload = await _generate_claim_advice(
                incident_snapshot=incident_snapshot,
                policy_snapshot=policy_snapshot,
                coverage=coverage,
                eligibility_notes=result.notes,
                required_doc_profile=required_doc_profile,
            )
            result.advice_text = advice_payload["advice_text"]
            result.recommended_actions = advice_payload["recommended_actions"]
            result.save_draft_available = advice_payload["save_option_available"]
            result.end_flow_available = advice_payload["end_flow_available"]
            advice_internal = {
                "input_snapshot": incident_snapshot,
                "coverage_ref": {
                    "claim_id": claim_id,
                    "outcome": result.outcome,
                    "next_action": result.next_action,
                },
                "generated_text": result.advice_text,
                "recommended_actions": result.recommended_actions,
                "generation_mode": advice_payload["generation_mode"],
                "generated_at": datetime.now(timezone.utc),
            }

    update_payload = {
        "eligibility": result.model_dump(),
        "coverage_precheck_internal": coverage_precheck_internal,
        "updated_at": datetime.now(timezone.utc),
    }
    if advice_internal is not None:
        update_payload["advice_internal"] = advice_internal

    update_doc: dict = {"$set": update_payload}
    if advice_internal is None:
        update_doc["$unset"] = {"advice_internal": ""}

    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        update_doc,
    )
    return result


@router.post("/{claim_id}/chat-bootstrap", response_model=ClaimChatBootstrapResponse)
async def bootstrap_claim_chat(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimChatBootstrapResponse:
    claim_doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not claim_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    eligibility_doc = claim_doc.get("eligibility")
    if not eligibility_doc:
        eligibility_result = await get_eligibility(claim_id=claim_id, user=user, db=db)
        eligibility_doc = eligibility_result.model_dump()
        claim_doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
        if not claim_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    if eligibility_doc.get("next_action") != "chat":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Claim is not eligible for chat guidance",
        )

    claim = ClaimInDB.from_mongo(claim_doc)
    vehicle = await _load_claim_vehicle(db, claim=claim, user_id=user.id)
    triage_doc = claim_doc.get("triage") or {}
    eligibility_result = EligibilityResponse.model_validate(eligibility_doc)
    required_doc_profile = await _build_required_doc_profile(db, claim=claim)
    context_seed = _build_chat_context_seed(
        claim=claim,
        vehicle=vehicle,
        triage_doc=triage_doc,
        eligibility_result=eligibility_result,
        required_doc_profile=required_doc_profile,
    )
    title = _build_chat_title(claim=claim, vehicle=vehicle)

    user_oid = ObjectId(user.id)
    now = datetime.now(timezone.utc)
    existing = await db["chat_sessions"].find_one(
        {
            "user_id": user_oid,
            "claim_id": claim_id,
            "workflow_stage": "claim_guidance",
        }
    )
    if existing:
        await db["chat_sessions"].update_one(
            {"_id": existing["_id"], "user_id": user_oid},
            {
                "$set": {
                    "title": title,
                    "context_seed": context_seed,
                    "seeded_from_eligibility": True,
                    "updated_at": now,
                }
            },
        )
        return ClaimChatBootstrapResponse(
            claim_id=claim_id,
            session_id=str(existing["_id"]),
            title=title,
            reused=True,
        )

    session_doc = {
        "user_id": user_oid,
        "title": title,
        "claim_id": claim_id,
        "workflow_stage": "claim_guidance",
        "context_seed": context_seed,
        "seeded_from_eligibility": True,
        "messages": [],
        "created_at": now,
        "updated_at": now,
    }
    result = await db["chat_sessions"].insert_one(session_doc)
    return ClaimChatBootstrapResponse(
        claim_id=claim_id,
        session_id=str(result.inserted_id),
        title=title,
        reused=False,
    )


@router.post("/{claim_id}/advice-action", response_model=ClaimAdviceActionResponse)
async def apply_claim_advice_action(
    claim_id: str,
    payload: ClaimAdviceActionRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimAdviceActionResponse:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    eligibility_doc = doc.get("eligibility") or {}
    if eligibility_doc.get("next_action") != "exit":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Advice actions are only available for exit decisions",
        )

    claim = ClaimInDB.from_mongo(doc)
    now = datetime.now(timezone.utc)

    if payload.action == "save_draft":
        timeline = _update_timeline_with_label(claim, label="Advice saved as draft", at=now)
        await db["claims"].update_one(
            {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
            {
                "$set": {
                    "status": "draft",
                    "timeline": timeline,
                    "advice_action": {"action": "save_draft", "at": now},
                    "updated_at": now,
                }
            },
        )
        return ClaimAdviceActionResponse(
            claim_id=claim_id,
            status="draft",
            message="Claim draft saved. You can return later to continue from the saved information.",
        )

    timeline = _update_timeline_with_label(claim, label="Claim closed without submission", at=now)
    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {
            "$set": {
                "status": "closed",
                "timeline": timeline,
                "closure_reason": "no_claim_advised",
                "advice_action": {"action": "end_flow", "at": now},
                "updated_at": now,
            }
        },
    )
    return ClaimAdviceActionResponse(
        claim_id=claim_id,
        status="closed",
        message="Claim flow closed. Your incident record has been kept for reference.",
    )


@router.post("/{claim_id}/first-notice", response_model=FirstNoticeResponse)
async def create_first_notice(
    claim_id: str,
    payload: FirstNoticeRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> FirstNoticeResponse:
    claim = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    now = datetime.now(timezone.utc)
    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {
            "$set": {
                "first_notice": {**payload.model_dump(), "at": now},
                "status": "needs-docs",
                "updated_at": now,
            }
        },
    )
    return FirstNoticeResponse(
        claim_id=claim_id,
        captured=True,
        message="First notice captured. Continue to evidence upload.",
    )


@router.get("/{claim_id}/dossier", response_model=DossierResponse)
async def build_dossier(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> DossierResponse:
    claim_doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not claim_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    claim = ClaimInDB.from_mongo(claim_doc)

    docs = await db["claim_documents"].find({"claim_id": ObjectId(claim_id)}).to_list(length=200)
    attachments_count = len([d for d in docs if d.get("upload_id")])
    required_map = {r.doc_type: r for r in required_docs_for_claim(claim)}
    completeness = "complete"
    for d in docs:
        r = required_map.get(d.get("doc_type"))
        if r and r.required and not d.get("upload_id"):
            completeness = "partial"
            break

    summary = f"Incident {claim.incident.type if claim.incident else 'unknown'} for vehicle {claim.vehicle_id}."
    timeline_items = [
        ValidationResultItem(doc_type=i.get("label", "timeline"), status="valid", note=i.get("status", ""))
        for i in claim_doc.get("timeline", [])
    ]
    return DossierResponse(
        claim_id=claim_id,
        summary=summary,
        timeline=timeline_items,
        attachments_count=attachments_count,
        completeness=completeness,
    )


@router.post("/{claim_id}/submit-router", response_model=SubmitRouterResponse)
async def submit_router(
    claim_id: str,
    payload: SubmitRouterRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> SubmitRouterResponse:
    claim_doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not claim_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    external_ref = f"SUB-{claim_id[-6:]}-{payload.channel.upper()}"
    now = datetime.now(timezone.utc)
    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {
            "$set": {
                "submission": {
                    "channel": payload.channel,
                    "external_ref": external_ref,
                    "status": "received",
                    "at": now,
                },
                "status": "processing",
                "updated_at": now,
            }
        },
    )
    return SubmitRouterResponse(
        claim_id=claim_id,
        channel=payload.channel,
        external_ref=external_ref,
        status="received",
    )


@router.post("/{claim_id}/appeal", response_model=ClaimAppealResponse)
async def appeal_claim(
    claim_id: str,
    payload: ClaimAppealRequest,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> ClaimAppealResponse:
    doc = await db["claims"].find_one({"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    claim = ClaimInDB.from_mongo(doc)
    timeline = [ClaimTimelineItem.model_validate(i).model_dump() for i in claim.timeline]
    now = datetime.now(timezone.utc)
    for i in timeline:
        if i.get("status") == "current":
            i["status"] = "done"
    timeline.append({"at": now, "label": "Appeal submitted", "status": "current"})

    await db["claims"].update_one(
        {"_id": ObjectId(claim_id), "user_id": ObjectId(user.id)},
        {
            "$set": {
                "appeal": {"reason": payload.reason, "at": now},
                "status": "processing",
                "timeline": timeline,
                "updated_at": now,
            }
        },
    )

    await db["notifications"].insert_one(
        {
            "user_id": ObjectId(user.id),
            "type": "info",
            "title": "Claim appeal submitted",
            "message": "Your appeal has been submitted and is under review.",
            "claim_id": ObjectId(claim_id),
            "read": False,
            "created_at": now,
        }
    )
    return ClaimAppealResponse(claim_id=claim_id, appealed=True, message="Appeal submitted")


@router.delete("/{claim_id}", response_model=OkResponse)
async def delete_claim(
    claim_id: str,
    user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
) -> OkResponse:
    try:
        claim_obj_id = ObjectId(claim_id)
        user_obj_id = ObjectId(user.id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid claim id")
    
    doc = await db["claims"].find_one({"_id": claim_obj_id, "user_id": user_obj_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    if doc.get("status") != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft claims can be deleted")
    
    res = await db["claims"].delete_one({"_id": claim_obj_id, "user_id": user_obj_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    await db["claim_documents"].delete_many({"claim_id": claim_obj_id})
    return OkResponse()

