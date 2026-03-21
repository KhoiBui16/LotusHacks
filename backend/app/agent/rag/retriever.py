"""
RAG Retriever Module cho policy/legal corpus trên Zilliz Cloud.

Retriever chỉ chịu trách nhiệm:
    1. index_documents()      — upsert chunks + metadata vào Zilliz
    2. retrieve()             — semantic retrieval không filter
    3. retrieve_with_filter() — semantic retrieval có filter metadata

Metadata runtime agent sử dụng ở mức tối thiểu: source / insurer / article / chunk_index.
Collection vẫn giữ cột `category` trống để tương thích với dữ liệu/collection cũ,
nhưng không còn populate bằng keyword heuristic và agent cũng không dựa vào nó.
"""
from typing import Any

from pymilvus import DataType, MilvusClient
from sentence_transformers import SentenceTransformer

from app.core.config import agent_settings


class PolicyRetriever:
    """
    RAG module sử dụng Zilliz Cloud để index và truy xuất policy documents.

    Workflow:
        1. index_documents()       — Embed text chunks và upsert vào Zilliz
        2. retrieve()              — Tìm kiếm semantic similarity (toàn pool)
        3. retrieve_with_filter()  — Tìm kiếm có filter metadata (vd. insurer)

    Embedding:
        sentence-transformers/paraphrase-multilingual-mpnet-base-v2
        (mặc định) — phù hợp tiếng Việt, chạy local CPU.

    Attributes:
        _client: MilvusClient instance cho Zilliz Cloud.
        _embed_model: SentenceTransformer singleton.
        _collection_ready: Đánh dấu schema/index đã được ensure.
    """

    _UPSERT_BATCH_SIZE = 128
    _PLACEHOLDER_MARKERS = (
        "YOUR_CLUSTER",
        "YOUR-CLUSTER",
        "YOUR_API_KEY",
        "YOUR_ZILLIZ",
        "example.invalid",
    )

    def __init__(self):
        """Khởi tạo lazy client/model để tránh gọi network khi import module."""
        self._client: MilvusClient | None = None
        self._embed_model: SentenceTransformer | None = None
        self._collection_ready = False

    @property
    def collection_name(self) -> str:
        return agent_settings.ZILLIZ_COLLECTION_NAME

    def _is_configured(self) -> bool:
        """Kiểm tra Zilliz URI + token đã được cấu hình hợp lệ chưa."""
        if self._client is not None:
            return True

        uri = agent_settings.ZILLIZ_URI.strip()
        token = agent_settings.ZILLIZ_TOKEN.strip()
        if not uri or not token:
            return False
        return not any(marker in uri or marker in token for marker in self._PLACEHOLDER_MARKERS)

    def _get_client(self) -> MilvusClient:
        """Lấy hoặc tạo MilvusClient."""
        if self._client is not None:
            return self._client

        if not self._is_configured():
            raise RuntimeError(
                "[RAG] Zilliz chưa được cấu hình đầy đủ. "
                "Cần có ZILLIZ_URI và ZILLIZ_TOKEN hợp lệ."
            )

        self._client = MilvusClient(
            uri=agent_settings.ZILLIZ_URI,
            token=agent_settings.ZILLIZ_TOKEN,
            timeout=agent_settings.ZILLIZ_TIMEOUT_SEC,
        )
        return self._client

    def _get_embed_model(self) -> SentenceTransformer:
        """Load embedding model theo cấu hình env (singleton)."""
        if self._embed_model is None:
            hf_token = agent_settings.HF_TOKEN or None
            self._embed_model = SentenceTransformer(
                agent_settings.ZILLIZ_EMBED_MODEL,
                token=hf_token,
            )
        return self._embed_model

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed danh sách text thành normalized vectors."""
        return self._get_embed_model().encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

    def _ensure_collection(self):
        """
        Tạo collection/schema/index trên Zilliz nếu chưa tồn tại.

        Schema cho corpus policy:
            id, vector, text, source, insurer, category(legacy), article, chunk_index
        """
        if self._collection_ready:
            return

        client = self._get_client()
        if client.has_collection(self.collection_name):
            self._collection_ready = True
            return

        schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field("id", DataType.VARCHAR, max_length=64, is_primary=True)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=agent_settings.ZILLIZ_EMBED_DIM)
        schema.add_field("text", DataType.VARCHAR, max_length=8192)
        schema.add_field("source", DataType.VARCHAR, max_length=256)
        schema.add_field("insurer", DataType.VARCHAR, max_length=64)
        schema.add_field("category", DataType.VARCHAR, max_length=64)
        schema.add_field("article", DataType.VARCHAR, max_length=64)
        schema.add_field("chunk_index", DataType.INT64)

        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="AUTOINDEX",
            metric_type="COSINE",
        )

        client.create_collection(
            collection_name=self.collection_name,
            schema=schema,
            index_params=index_params,
        )
        self._collection_ready = True

    def _get_total_chunks(self) -> int:
        """Đếm tổng số vectors hiện có trong collection."""
        client = self._get_client()
        if not client.has_collection(self.collection_name):
            return 0

        stats = client.get_collection_stats(self.collection_name)
        return int(stats.get("row_count", 0))

    def _format_filter_value(self, value: Any) -> str:
        """Chuyển Python value sang literal cho Zilliz filter expression."""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)

        safe_value = str(value).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{safe_value}"'

    def _build_filter_expression(self, where: dict | None) -> str:
        """
        Chuyển dict-style filter cũ sang biểu thức filter của Zilliz.

        Hỗ trợ:
            {"insurer": "PTI"}
            {"$and": [{"insurer": "PTI"}, {"article": "Điều 7"}]}
            {"$or": [{"insurer": "PTI"}, {"insurer": "MIC"}]}
        """
        if not where:
            return ""

        if "$and" in where:
            parts = [self._build_filter_expression(part) for part in where["$and"] if part]
            parts = [part for part in parts if part]
            return " and ".join(f"({part})" for part in parts)

        if "$or" in where:
            parts = [self._build_filter_expression(part) for part in where["$or"] if part]
            parts = [part for part in parts if part]
            return " or ".join(f"({part})" for part in parts)

        clauses = []
        for key, value in where.items():
            if value is None:
                continue
            clauses.append(f"{key} == {self._format_filter_value(value)}")
        return " and ".join(clauses)

    def _normalise_metadata(self, metadata: dict | None) -> dict[str, Any]:
        """Ép metadata về schema cố định để upsert vào Zilliz."""
        metadata = metadata or {}
        return {
            "source": str(metadata.get("source", "unknown")),
            "insurer": str(metadata.get("insurer", "")),
            "category": str(metadata.get("category", "")),
            "article": str(metadata.get("article", "")),
            "chunk_index": int(metadata.get("chunk_index", 0)),
        }

    def _search(self, query: str, filter_expression: str = "", k: int = 5) -> list[dict[str, Any]]:
        """Thực hiện semantic search trên Zilliz và trả về hits đã chuẩn hóa."""
        self._ensure_collection()
        total_chunks = self._get_total_chunks()
        if total_chunks == 0:
            return []

        client = self._get_client()
        query_vector = self._embed_texts([query])[0]
        raw_results = client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            limit=min(k, total_chunks),
            filter=filter_expression,
            output_fields=["text", "source", "insurer", "article", "chunk_index"],
            search_params={"metric_type": "COSINE"},
        )

        hits: list[dict[str, Any]] = []
        for hit in raw_results[0]:
            entity = hit.get("entity", {})
            hits.append(
                {
                    "id": str(hit.get("id", entity.get("id", ""))),
                    "text": entity.get("text", ""),
                    "source": entity.get("source", ""),
                    "insurer": entity.get("insurer", ""),
                    "article": entity.get("article", ""),
                    "chunk_index": entity.get("chunk_index", 0),
                    "score": float(hit.get("distance", 0.0)),
                }
            )
        return hits

    def _hit_to_citation(self, hit: dict[str, Any]) -> dict[str, Any]:
        """Chuẩn hóa hit thành citation metadata để trả ra agent/workflow."""
        return {
            "chunk_id": hit.get("id", ""),
            "source": hit.get("source", ""),
            "article": hit.get("article", ""),
            "insurer": hit.get("insurer", ""),
            "score": round(float(hit.get("score", 0.0)), 4),
        }

    def _hits_to_citations(self, hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Loại duplicate và trả về danh sách citations ngắn gọn."""
        citations = []
        seen = set()

        for hit in hits:
            citation = self._hit_to_citation(hit)
            dedupe_key = (
                citation["chunk_id"],
                citation["source"],
                citation["article"],
            )
            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            citations.append(citation)

        return citations

    def _hits_to_context(self, hits: list[dict[str, Any]]) -> str:
        """Format context kèm citation metadata để LLM có thể dẫn chiếu điều khoản."""
        if not hits:
            return "[RAG] Không tìm thấy tài liệu liên quan."

        parts = []
        for index, hit in enumerate(hits, 1):
            article = hit.get("article") or "N/A"
            score = float(hit.get("score", 0.0))
            header = (
                f"[Citation {index}] "
                f"source={hit.get('source', '')} | "
                f"insurer={hit.get('insurer', '')} | "
                f"article={article} | "
                f"chunk_id={hit.get('id', '')} | "
                f"score={score:.4f}"
            )
            parts.append(f"{header}\n{hit.get('text', '')}")

        return "\n\n---\n\n".join(parts)

    def index_documents(
        self,
        texts: list[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
    ):
        """
        Index danh sách text chunks vào Zilliz.

        Dùng upsert để tránh duplicate khi re-index cùng chunk_id.
        """
        if not texts:
            print("[RAG] Không có chunk nào để index.")
            return

        self._ensure_collection()

        if ids is None:
            ids = [f"chunk_{i}" for i in range(len(texts))]
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in texts]

        if len(texts) != len(ids) or len(texts) != len(metadatas):
            raise ValueError("texts, metadatas và ids phải có cùng số lượng phần tử.")

        vectors = self._embed_texts(texts)
        rows = []
        for text, metadata, chunk_id, vector in zip(texts, metadatas, ids, vectors):
            row = self._normalise_metadata(metadata)
            row.update(
                {
                    "id": str(chunk_id),
                    "vector": vector,
                    "text": text,
                }
            )
            rows.append(row)

        client = self._get_client()
        for start in range(0, len(rows), self._UPSERT_BATCH_SIZE):
            batch = rows[start:start + self._UPSERT_BATCH_SIZE]
            client.upsert(collection_name=self.collection_name, data=batch)

        print(f"[RAG] Indexed {len(texts)} chunks into collection '{self.collection_name}'.")

    def retrieve(self, query: str, k: int = 5) -> str:
        """
        Truy xuất context liên quan từ Zilliz (toàn bộ pool, không filter).

        Backward-compatible với code cũ.
        """
        context, _ = self.retrieve_details(query=query, k=k)
        return context

    def retrieve_details(
        self,
        query: str,
        k: int = 5,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Trả về context + citation metadata cho truy xuất không filter."""
        if not self._is_configured():
            return (
                "[RAG] Zilliz chưa được cấu hình. "
                "Vui lòng cập nhật ZILLIZ_URI và ZILLIZ_TOKEN.",
                [],
            )

        try:
            hits = self._search(query=query, k=k)
        except Exception as exc:
            return f"[RAG] Zilliz retrieval failed: {exc}", []

        if not hits:
            return "[RAG] Không tìm thấy tài liệu liên quan.", []

        return self._hits_to_context(hits), self._hits_to_citations(hits)

    def retrieve_with_filter(
        self,
        query: str,
        where: dict | None = None,
        k: int = 5,
    ) -> tuple[str, list[str]]:
        """
        Truy xuất context từ Zilliz có filter theo metadata.

        Dùng cho các trường hợp cần semantic search trên một tập policy con
        như insurer/source/article cụ thể.
        """
        context, citations = self.retrieve_with_filter_details(query=query, where=where, k=k)
        chunk_ids = [citation["chunk_id"] for citation in citations if citation.get("chunk_id")]
        return context, chunk_ids

    def retrieve_with_filter_details(
        self,
        query: str,
        where: dict | None = None,
        k: int = 5,
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Trả về context + citation metadata cho truy xuất có filter.

        Dùng cho Agent 1/Agent 2 khi cần trace source/article/chunk_id.
        """
        if not self._is_configured():
            return (
                "[RAG] Zilliz chưa được cấu hình. "
                "Vui lòng cập nhật ZILLIZ_URI và ZILLIZ_TOKEN.",
                [],
            )

        filter_expression = self._build_filter_expression(where)
        try:
            hits = self._search(query=query, filter_expression=filter_expression, k=k)
            if not hits and filter_expression:
                hits = self._search(query=query, filter_expression="", k=k)
        except Exception:
            try:
                hits = self._search(query=query, filter_expression="", k=k)
            except Exception as exc:
                return f"[RAG] Zilliz retrieval failed: {exc}", []

        if not hits:
            return "[RAG] Không tìm thấy tài liệu liên quan.", []

        return self._hits_to_context(hits), self._hits_to_citations(hits)

    def get_stats(self) -> dict:
        """
        Trả về thống kê collection hiện tại.

        Returns:
            dict: Gồm vector_backend, collection_name, total_chunks, zilliz_uri,
                  zilliz_configured và embedding_model.
        """
        stats = {
            "vector_backend": "zilliz",
            "collection_name": self.collection_name,
            "total_chunks": 0,
            "zilliz_uri": agent_settings.ZILLIZ_URI,
            "zilliz_configured": self._is_configured(),
            "embedding_model": agent_settings.ZILLIZ_EMBED_MODEL,
        }

        if not stats["zilliz_configured"]:
            return stats

        try:
            stats["total_chunks"] = self._get_total_chunks()
        except Exception as exc:
            stats["error"] = str(exc)

        return stats


# Singleton instance — dùng chung cho toàn bộ application
policy_retriever = PolicyRetriever()
