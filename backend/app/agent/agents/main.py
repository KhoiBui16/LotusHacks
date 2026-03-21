import json
import logging
import os
from typing import Any

from dotenv import load_dotenv

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

from app.agent.agents.checklist_generation import (
    format_context,
    get_embedding,
    retrieve_chunks,
    checklist_generate,
)


load_dotenv()
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPEN_AI_MODEL = os.getenv("CHAT_LLM_MODEL", "gpt-4o-mini")

CHECKLIST_KEYWORDS = [
    "ho so",
    "hồ sơ",
    "giay to",
    "giấy tờ",
    "bien ban",
    "biên bản",
    "chung tu",
    "chứng từ",
    "can nop",
    "cần nộp",
    "chuan bi gi",
    "chuẩn bị gì",
    "nop gi",
    "nộp gì",
]

_client: Any = None


def _get_openai_client() -> Any:
    global _client
    if OpenAI is None:
        raise RuntimeError("openai package is not installed")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def is_checklist_query(query: str) -> bool:
    q = query.lower()
    return any(keyword in q for keyword in CHECKLIST_KEYWORDS)


def intent_detection(query: str) -> dict[str, Any]:
    system_prompt = """
    (In English)
    You are an intent classifier for an insurance AI system.

    Return ONLY valid JSON with this schema:

    {
      "intent": "claim_document_checklist | policy_explanation | claim_process_steps | unknown",
      "insurance_company": "string|null",
      "confidence": float,
      "reason": "short explanation"
    }

    Rules:
    - If user asks about required documents, paperwork, what to submit -> intent = claim_document_checklist
    - If user asks about rules, explanation, coverage -> intent = policy_explanation
    - If asking steps/process -> claim_process_steps
    - If unclear -> unknown

    Do NOT answer the question. Only classify.

    (In Vietnamese)
    Bạn là bộ phân loại ý định cho hệ thống AI bảo hiểm.
    Chỉ trả về JSON hợp lệ với lược đồ sau:

    {
      "intent": "claim_document_checklist | policy_explanation | claim_process_steps | unknown",
      "insurance_company": "string|null",
      "confidence": float,
      "reason": "short explanation"
    }

    Quy tắc:
    - Nếu người dùng hỏi về các tài liệu cần thiết, giấy tờ, những gì cần nộp -> intent = claim_document_checklist
    - Nếu người dùng hỏi về các quy tắc, giải thích, phạm vi bảo hiểm -> intent = policy_explanation
    - Nếu hỏi về các bước/quy trình -> claim_process_steps
    - Nếu không rõ ràng -> unknown
    KHÔNG trả lời câu hỏi. Chỉ phân loại.
    """

    client = _get_openai_client()
    response = client.chat.completions.create(
        model=OPEN_AI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        temperature=0,
    )

    try:
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception:
        return {
            "intent": "unknown",
            "insurance_company": None,
            "confidence": 0.3,
            "reason": "parse_error",
        }


def call_llm_rag(context: str, query: str) -> str:
    system_prompt = """\
    You are an expert insurance claim assistant for the VETC platform in Vietnam.

    You will be given:
    - Claim context (insurer, incident type, severity, flags)
    - Retrieved policy clauses from the insurer's documents
    - Mandatory business rules already pre-evaluated

    Your job:
    - Answer user questions based ONLY on the provided policy context
    - Explain rules, coverage, exclusions clearly
    - Cite sources when possible

    Rules:
    - Base requirements strictly on retrieved policy clauses
    - Be specific to the named insurer and never generalize across insurers
    """

    user_prompt = f"""
    Context:
    {context}

    User Query:
    {query}
    """

    client = _get_openai_client()
    response = client.chat.completions.create(
        model=OPEN_AI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content or ""


def rag_tool(query: str) -> dict[str, Any]:
    try:
        chunks = retrieve_chunks(query, top_k=7)
        if not chunks:
            return {"error": "No relevant documents found"}

        context = format_context(chunks)
        raw = call_llm_rag(context, query)

        return {
            "source": "rag_tool",
            "answer": raw,
        }
    except Exception as exc:
        logger.exception("rag_tool failed")
        return {"error": str(exc)}


def route_query(query: str) -> dict[str, Any]:
    if is_checklist_query(query):
        return {
            "route": "checklist_tool_rule",
            "data": checklist_generate(query),
        }

    intent_data = intent_detection(query)
    intent = intent_data.get("intent")

    if intent == "claim_document_checklist":
        return {
            "route": "checklist_tool",
            "data": checklist_generate(query),
        }

    return {
        "route": "rag_tool",
        "data": rag_tool(query),
    }


def _render_route_result(result: dict[str, Any]) -> tuple[str, str | None]:
    route = result.get("route")
    data = result.get("data") if isinstance(result, dict) else None

    if route in {"checklist_tool", "checklist_tool_rule"} and isinstance(data, dict):
        checklist = data.get("checklist")
        if isinstance(checklist, dict):
            return json.dumps(checklist, ensure_ascii=False, indent=2), str(route)
        if isinstance(checklist, str) and checklist.strip():
            return checklist, str(route)
        if data.get("error"):
            return f"Không thể tạo checklist lúc này: {data.get('error')}", str(route)

    if route == "rag_tool" and isinstance(data, dict):
        answer = data.get("answer")
        if isinstance(answer, str) and answer.strip():
            return answer, str(route)
        if data.get("error"):
            return f"Mình chưa truy xuất được tri thức chính sách: {data.get('error')}", str(route)

    return "Mình chưa xử lý được yêu cầu này. Bạn thử diễn đạt lại hoặc cung cấp thêm ngữ cảnh sự cố/đơn bảo hiểm.", None


def generate_chat_answer_with_meta(query: str) -> dict[str, Any]:
    result = route_query(query)
    content, source_tool = _render_route_result(result)
    return {
        "content": content,
        "source_tool": source_tool,
    }


def generate_chat_answer(query: str) -> str:
    return str(generate_chat_answer_with_meta(query).get("content", ""))
