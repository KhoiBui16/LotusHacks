"""
Script index policy text vào Zilliz Cloud.

Notebook mẫu chỉ được dùng để tham khảo cách kết nối Zilliz, không áp dụng
taxonomy chunk bằng keyword vào RAG nghiệp vụ của project này.

Pipeline index hiện tại:
    1. Đọc tất cả file `policy_*.txt`
    2. Split theo paragraph + overlap
    3. Gắn metadata trung tính: source, insurer, article, chunk_index
    4. Upsert lên Zilliz

Agent sẽ tự suy luận từ context retrieve được, thay vì dựa vào nhãn chunk tự sinh.
"""
import hashlib
import os
import re
import sys

from app.agent.rag.retriever import policy_retriever


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _safe_print(message: str):
    """In log an toàn trên Windows khi terminal không support Unicode đầy đủ."""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode(encoding, errors="replace").decode(encoding, errors="replace"))


def _detect_article(chunk_text: str) -> str:
    """
    Trích xuất số Điều (article) từ chunk text.

    Tìm pattern "Điều X" hoặc "Điều XX" trong text.
    Nếu nhiều Điều trong 1 chunk, lấy Điều đầu tiên.
    """
    match = re.search(r"(Điều\s+\d+)", chunk_text)
    return match.group(1) if match else ""


def split_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """
    Split text thành các chunks với overlap.

    Chiến lược:
    1. Split theo đoạn (double newline) trước — giữ nguyên structure
    2. Nếu đoạn vượt chunk_size → bắt đầu chunk mới
    3. Overlap 150 chars với chunk trước để giữ context liền mạch
    """
    paragraphs = re.split(r"\n\n+", text)
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk += ("\n\n" + para) if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            if overlap > 0 and current_chunk:
                overlap_text = current_chunk[-overlap:]
                current_chunk = overlap_text + "\n\n" + para
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _build_chunk_id(source_name: str, chunk_index: int, chunk_text: str) -> str:
    """Sinh ID ổn định để re-index không tạo duplicate trên Zilliz."""
    raw = f"{source_name}:{chunk_index}:{chunk_text[:64]}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def index_text_policies():
    """
    Load và index tất cả file policy_*.txt vào Zilliz.

    Workflow:
    1. Scan thư mục data/ tìm file policy_*.txt
    2. Đọc + split mỗi file thành chunks
    3. Gắn metadata trung tính: source, insurer, article, chunk_index
    4. Upsert tất cả chunks vào Zilliz collection 'insurance_policies'
    """
    text_files = [
        f for f in os.listdir(DATA_DIR)
        if f.startswith("policy_") and f.endswith(".txt")
    ]

    if not text_files:
        _safe_print(f"[Index] Khong tim thay file policy nao trong {DATA_DIR}")
        return

    all_chunks = []
    all_metadatas = []
    all_ids = []

    for fname in sorted(text_files):
        path = os.path.join(DATA_DIR, fname)
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()

        insurer = fname.replace("policy_", "").replace(".txt", "").upper()
        chunks = split_text(content, chunk_size=800, overlap=150)
        _safe_print(f"[Index] {fname}: {len(chunks)} chunks (insurer: {insurer})")

        for chunk_index, chunk in enumerate(chunks):
            article = _detect_article(chunk)
            chunk_id = _build_chunk_id(fname, chunk_index, chunk)

            all_chunks.append(chunk)
            all_metadatas.append(
                {
                    "source": fname,
                    "insurer": insurer,
                    "article": article,
                    "chunk_index": chunk_index,
                }
            )
            all_ids.append(chunk_id)

            article_info = f", {article}" if article else ""
            _safe_print(f"  [chunk {chunk_index}]{article_info}")

    policy_retriever.index_documents(
        texts=all_chunks,
        metadatas=all_metadatas,
        ids=all_ids,
    )

    stats = policy_retriever.get_stats()
    _safe_print(f"[Index] Hoan tat! Total chunks: {stats['total_chunks']}")
    _safe_print(f"[Index] Vector backend: {stats['vector_backend']}")
    _safe_print(f"[Index] Collection: {stats['collection_name']}")
    if stats.get("zilliz_uri"):
        _safe_print(f"[Index] Zilliz URI: {stats['zilliz_uri']}")


if __name__ == "__main__":
    index_text_policies()
