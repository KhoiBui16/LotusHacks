import json
import logging
import os
import re
from typing import Any

from dotenv import load_dotenv

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

try:
    from pymilvus import Collection, connections
except ModuleNotFoundError:
    Collection = None
    connections = None

try:
    from sentence_transformers import SentenceTransformer
except ModuleNotFoundError:
    SentenceTransformer = None


load_dotenv()
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ZILLIZ_TOKEN = os.getenv("ZILLIZ_TOKEN")
MILVUS_HOST = os.getenv("MILVUS_HOST")
COLLECTION_NAME = "vetc_policy_json"
EMBEDDED_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
OPEN_AI_MODEL = os.getenv("CHAT_LLM_MODEL", "gpt-4o-mini")

_client: Any = None
_embed_model: Any = None
_collection: Any = None
_milvus_connected = False


def _get_openai_client() -> Any:
    global _client
    if OpenAI is None:
        raise RuntimeError("openai package is not installed")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _get_embed_model() -> Any:
    global _embed_model
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers package is not installed")
    if _embed_model is None:
        _embed_model = SentenceTransformer(EMBEDDED_MODEL)
    return _embed_model


def _get_collection() -> Any:
    global _collection, _milvus_connected
    if Collection is None or connections is None:
        raise RuntimeError("pymilvus package is not installed")
    if not MILVUS_HOST or not ZILLIZ_TOKEN:
        raise RuntimeError("MILVUS_HOST/ZILLIZ_TOKEN is not configured")

    if not _milvus_connected:
        connections.connect(alias="default", uri=MILVUS_HOST, token=ZILLIZ_TOKEN)
        _milvus_connected = True

    if _collection is None:
        _collection = Collection(COLLECTION_NAME)

    return _collection


def get_embedding(text: str) -> list[float]:
    model = _get_embed_model()
    return model.encode(text, normalize_embeddings=True).tolist()


def call_llm(context: str, query: str) -> str:
    client = _get_openai_client()
    system_prompt_ver1 = """\
    You are an expert insurance claim assistant for the VETC platform in Vietnam.
    Your task is to generate a personalized document checklist for an insurance claim.

    You will be given:
    - Claim context (insurer, incident type, severity, flags)
    - Retrieved policy clauses from the insurer's documents
    - Mandatory business rules already pre-evaluated

    Output ONLY a valid JSON object with this exact structure:
    {
    "required_documents": [
        {"document": "<name>", "reason": "<why required>", "notes": "<how to obtain>"}
    ],
    "conditional_documents": [
        {"document": "<name>", "condition": "<when required>", "reason": "<why>"}
    ],
    "optional_documents": [
        {"document": "<name>", "benefit": "<why this helps the claim>"}
    ],
    "special_notes": "<insurer-specific or incident-specific warnings>",
    "estimated_processing_time": "<X working days>",
    "sources_used": ["<source filenames>"]
    }

    Rules:
    - Base requirements strictly on retrieved policy clauses
    - Apply all pre-evaluated business rule flags without override
    - Be specific to the named insurer and never generalize across insurers
    - Respond ONLY with the JSON object, no preamble or markdown fences
    """
    
    system_prompt_ver2 = """\
    You are an expert insurance claim assistant for the VETC platform in Vietnam.
    Your task is to generate a personalized document checklist for an insurance claim in markdown format.

    You will be given:
    - Claim context (insurer, incident type, severity, flags)
    - Retrieved policy clauses from the insurer's documents
    - Mandatory business rules already pre-evaluated

    Format your response as proper markdown:
    
    # Required Documents
    - **<document name>**: <why required>. <how to obtain>
    - **<document name>**: <why required>. <how to obtain>
    
    # Additional Documents (if applicable)
    - **<document name>**: Required when <condition>. <why it helps>
    - **<document name>**: Required when <condition>. <why it helps>
    
    # Optional Documents
    - **<document name>**: <benefit of including>
    - **<document name>**: <benefit of including>
    
    # Important Notes
    - <insurer-specific warning or special condition>
    - <insurer-specific warning or special condition>
    
    # Processing Timeline
    Estimated **X working days** for processing.

    Rules:
    - Base requirements strictly on retrieved policy clauses
    - Apply all pre-evaluated business rule flags without override
    - Be specific to the named insurer and never generalize across insurers
    - Output ONLY markdown format with proper `#` headers and `-` bullet points
    - Use **bold** for document names
    - Keep explanations concise and informative
    - Ensure markdown is valid and properly formatted
    """

    user_prompt = f"""
    Context:
    {context}

    User Query:
    {query}
    """

    response = client.chat.completions.create(
        model=OPEN_AI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt_ver2},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content or ""


def format_context(chunks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[Source {i}: {c['source']}, Score: {c['score']:.2f}]\n"
            f"{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


def retrieve_chunks(query: str, top_k: int = 7) -> list[dict[str, Any]]:
    collection = _get_collection()
    query_vector = get_embedding(query)

    results = collection.search(
        data=[query_vector],
        anns_field="vector",
        param={"metric_type": "COSINE", "params": {"nprobe": 10}},
        limit=top_k,
        output_fields=["text", "source"],
    )

    chunks: list[dict[str, Any]] = []
    for hit in results[0]:
        entity = hit.entity
        chunks.append(
            {
                "text": entity.get("text"),
                "source": entity.get("source"),
                #"page": entity.get("page"),
                "score": round(hit.distance, 4),
            }
        )

    return chunks


def safe_parse_json(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        return {
            "error": "invalid_json_from_llm",
            "raw_output": cleaned,
        }
        
        



def checklist_generate(query: str, top_k: int = 7) -> dict[str, Any]:
    try:
        chunks = retrieve_chunks(query, top_k)
        if not chunks:
            return {"error": "No relevant documents found"}

        context = format_context(chunks)
        raw = call_llm(context, query)
        # checklist = safe_parse_json(raw)

        return {
            "query": query,
            "checklist": raw,
            "retrieval_count": len(chunks),
        }
    except Exception as exc:
        logger.exception("checklist_generate failed")
        return {"error": str(exc)}
