"""
Unit tests cho RAG Retriever module (Zilliz-backed contract).
"""
import math
import re

import pytest

from app.agent.rag.retriever import PolicyRetriever


class FakeSchema:
    """Schema giả cho Milvus client test double."""

    def __init__(self):
        self.fields = []

    def add_field(self, field_name, data_type, **kwargs):
        self.fields.append((field_name, data_type, kwargs))


class FakeIndexParams:
    """Index params giả cho Milvus client test double."""

    def __init__(self):
        self.indexes = []

    def add_index(self, **kwargs):
        self.indexes.append(kwargs)


class FakeMilvusClient:
    """In-memory Zilliz/Milvus-compatible client cho unit tests."""

    def __init__(self):
        self.collections: dict[str, list[dict]] = {}

    def has_collection(self, collection_name: str) -> bool:
        return collection_name in self.collections

    def create_schema(self, **kwargs):
        return FakeSchema()

    def prepare_index_params(self):
        return FakeIndexParams()

    def create_collection(self, collection_name: str, schema, index_params):
        self.collections.setdefault(collection_name, [])

    def get_collection_stats(self, collection_name: str) -> dict:
        return {"row_count": len(self.collections.get(collection_name, []))}

    def upsert(self, collection_name: str, data: list[dict]):
        collection = self.collections.setdefault(collection_name, [])
        index_by_id = {row["id"]: idx for idx, row in enumerate(collection)}

        for row in data:
            if row["id"] in index_by_id:
                collection[index_by_id[row["id"]]] = row
            else:
                collection.append(row)

    def query(
        self,
        collection_name: str,
        filter: str = "",
        output_fields: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict]:
        rows = [
            row for row in self.collections.get(collection_name, [])
            if self._matches_filter(row, filter)
        ][:limit]

        if not output_fields:
            return [dict(row) for row in rows]

        results = []
        for row in rows:
            result = {field: row.get(field) for field in output_fields}
            if "id" in output_fields:
                result["id"] = row["id"]
            results.append(result)
        return results

    def search(
        self,
        collection_name: str,
        data: list[list[float]],
        limit: int,
        filter: str = "",
        output_fields: list[str] | None = None,
        search_params: dict | None = None,
    ) -> list[list[dict]]:
        query_vector = data[0]
        rows = [
            row for row in self.collections.get(collection_name, [])
            if self._matches_filter(row, filter)
        ]

        hits = []
        for row in rows:
            score = self._cosine(query_vector, row["vector"])
            entity = {field: row.get(field) for field in (output_fields or [])}
            hits.append(
                {
                    "id": row["id"],
                    "distance": score,
                    "entity": entity,
                }
            )

        hits.sort(key=lambda hit: hit["distance"], reverse=True)
        return [hits[:limit]]

    def _matches_filter(self, row: dict, filter_expression: str) -> bool:
        if not filter_expression:
            return True

        expression = filter_expression.replace("(", "").replace(")", "")
        or_parts = [part.strip() for part in expression.split(" or ") if part.strip()]
        return any(self._matches_and(row, part) for part in or_parts)

    def _matches_and(self, row: dict, expression: str) -> bool:
        and_parts = [part.strip() for part in expression.split(" and ") if part.strip()]
        return all(self._evaluate_clause(row, clause) for clause in and_parts)

    def _evaluate_clause(self, row: dict, clause: str) -> bool:
        match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*==\s*(.+)", clause)
        if not match:
            return False

        field_name, raw_value = match.groups()
        raw_value = raw_value.strip()

        if raw_value.startswith('"') and raw_value.endswith('"'):
            value = raw_value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        elif raw_value in {"true", "false"}:
            value = raw_value == "true"
        else:
            try:
                value = int(raw_value)
            except ValueError:
                value = float(raw_value)

        return row.get(field_name) == value

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)


def _vectorize(text: str) -> list[float]:
    """Embedding giả nhưng đủ ổn định để test ranking/filter."""
    lower_text = text.lower()
    accident_signal = sum(lower_text.count(token) for token in ["va chạm", "tai nạn", "xe"])
    exclusion_signal = sum(lower_text.count(token) for token in ["loại trừ", "rượu", "bằng lái", "gplx"])
    coverage_signal = sum(lower_text.count(token) for token in ["phạm vi", "bồi thường", "bảo hiểm"])
    length_signal = max(len(lower_text), 1) / 1000
    return [accident_signal, exclusion_signal, coverage_signal, length_signal]


@pytest.fixture
def temp_retriever():
    """Tạo PolicyRetriever với fake Milvus client."""
    retriever = PolicyRetriever.__new__(PolicyRetriever)
    retriever._client = FakeMilvusClient()
    retriever._embed_model = None
    retriever._collection_ready = False
    retriever._embed_texts = lambda texts: [_vectorize(text) for text in texts]
    return retriever


class TestPolicyRetriever:
    """Test PolicyRetriever class."""

    def test_init_contract(self, temp_retriever):
        """Test khởi tạo retriever stubbed."""
        assert temp_retriever._client is not None

    def test_get_collection_creates_zilliz_collection(self, temp_retriever):
        """Test ensure collection trên client giả."""
        temp_retriever._ensure_collection()
        assert temp_retriever._client.has_collection(temp_retriever.collection_name) is True

    def test_index_and_retrieve(self, temp_retriever):
        """Test index documents rồi retrieve semantic context."""
        texts = [
            "Bảo hiểm vật chất xe ô tô bao gồm va chạm, đâm, lật xe.",
            "Trường hợp loại trừ: lái xe khi say rượu, không có bằng lái.",
            "Phạm vi bảo hiểm: thiệt hại do tai nạn giao thông.",
        ]
        metadatas = [
            {"source": "test_policy.txt", "insurer": "TEST", "article": "Điều 2"},
            {"source": "test_policy.txt", "insurer": "TEST", "article": "Điều 4"},
            {"source": "test_policy.txt", "insurer": "TEST", "article": "Điều 5"},
        ]
        ids = ["test_0", "test_1", "test_2"]

        temp_retriever.index_documents(texts=texts, metadatas=metadatas, ids=ids)

        stats = temp_retriever.get_stats()
        assert stats["total_chunks"] == 3
        assert stats["vector_backend"] == "zilliz"

        result = temp_retriever.retrieve("tai nạn va chạm xe", k=2)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Chưa có tài liệu" not in result

    def test_retrieve_with_filter(self, temp_retriever):
        """Test retrieve_with_filter giữ được metadata filter contract cũ."""
        temp_retriever.index_documents(
            texts=[
                "Điều 8 hướng dẫn xử lý tai nạn liên hoàn và cao tốc.",
                "Điều 2 PTI cho va chạm nhẹ.",
                "Điều 2 MIC cho ngập nước.",
            ],
            metadatas=[
                {"source": "a.txt", "insurer": "COMMON", "article": "Điều 8"},
                {"source": "pti.txt", "insurer": "PTI", "article": "Điều 2"},
                {"source": "mic.txt", "insurer": "MIC", "article": "Điều 2"},
            ],
            ids=["c1", "c2", "c3"],
        )

        context, chunk_ids = temp_retriever.retrieve_with_filter(
            query="quyền lợi PTI khi va chạm nhẹ",
            where={"$and": [{"insurer": "PTI"}, {"article": "Điều 2"}]},
            k=2,
        )

        assert "PTI" in context
        assert chunk_ids == ["c2"]

    def test_retrieve_with_filter_details_returns_citations(self, temp_retriever):
        """Test retriever trả về citation metadata thật để agent trace policy."""
        temp_retriever.index_documents(
            texts=["Điều 4 PTI: loại trừ khi say rượu."],
            metadatas=[{"source": "policy_pti.txt", "insurer": "PTI", "article": "Điều 4"}],
            ids=["pti_ex_1"],
        )

        context, citations = temp_retriever.retrieve_with_filter_details(
            query="nồng độ cồn PTI",
            where={"insurer": "PTI"},
            k=1,
        )

        assert "[Citation 1]" in context
        assert citations[0]["source"] == "policy_pti.txt"
        assert citations[0]["article"] == "Điều 4"
        assert citations[0]["chunk_id"] == "pti_ex_1"

    def test_retrieve_empty_collection(self, temp_retriever):
        """Test retrieve khi chưa có documents."""
        result = temp_retriever.retrieve("test query")
        assert "Không tìm thấy tài liệu" in result

    def test_get_stats_empty(self, temp_retriever):
        """Test stats khi collection rỗng."""
        stats = temp_retriever.get_stats()
        assert stats["total_chunks"] == 0
        assert stats["collection_name"] == "insurance_policies"
        assert stats["vector_backend"] == "zilliz"

    def test_index_documents_upsert(self, temp_retriever):
        """Test upsert: index cùng ID không tạo duplicate."""
        temp_retriever.index_documents(texts=["Document 1"], ids=["doc_1"])
        assert temp_retriever.get_stats()["total_chunks"] == 1

        temp_retriever.index_documents(texts=["Document 1 updated"], ids=["doc_1"])
        assert temp_retriever.get_stats()["total_chunks"] == 1

    def test_build_filter_expression(self, temp_retriever):
        """Test chuyển dict filter sang syntax Zilliz."""
        expression = temp_retriever._build_filter_expression(
            {"$and": [{"insurer": "PTI"}, {"article": "Điều 7"}]}
        )
        assert expression == '(insurer == "PTI") and (article == "Điều 7")'


class TestTextSplitter:
    """Test text splitting function."""

    def test_split_text_basic(self):
        """Test split text cơ bản."""
        from app.agent.rag.index_policies import split_text

        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        chunks = split_text(text, chunk_size=50, overlap=0)
        assert len(chunks) >= 1
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_split_text_long(self):
        """Test split text dài thành nhiều chunks."""
        from app.agent.rag.index_policies import split_text

        text = "\n\n".join([f"Đoạn văn số {index} với nội dung dài." * 5 for index in range(20)])
        chunks = split_text(text, chunk_size=200, overlap=50)
        assert len(chunks) > 1

    def test_split_text_empty(self):
        """Test split text rỗng."""
        from app.agent.rag.index_policies import split_text

        chunks = split_text("", chunk_size=100, overlap=0)
        assert len(chunks) == 0
