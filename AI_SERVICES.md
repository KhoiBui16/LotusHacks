# LotusHacks AI Services

File này là bản tóm tắt ngắn cho workflow AI phase hiện tại.

## Scope đang build

Phần đã được tích hợp vào `main`:

- FE giữ nguyên flow `StartClaim -> IncidentIntake`
- 7 bước intake của `IncidentIntake` được lưu theo schema claim hiện tại của BE
- cuối step 7, FE gọi `POST /claims/{claim_id}/triage`
- BE map claim thật sang input của workflow agent
- decision thật từ agent dùng để route:
  - `assisted_mode = true` -> `/assisted-mode`
  - `assisted_mode = false` -> `/chat`

Phần chưa mở rộng ở phase này:

- OCR/import policy tự động
- full coverage flow trên FE
- dossier builder
- submission router
- workflow tracking

## Vai trò của 2 agent

### Agent 1 - Triage

Input:

- thời gian
- địa điểm / GPS
- mô tả sự cố
- có bên thứ ba hay không
- xe còn chạy được hay không
- có người bị thương hay không
- một phần policy linkage từ claim/vehicle thật

Output:

- `is_complex`
- `description`
- `triggered_rules`
- `citations`

Tích hợp hiện tại:

- kết quả này được map về `TriageResponse` của `main`
- FE chỉ dùng `assisted_mode` để route

### Agent 2 - Coverage Pre-check

Input:

- toàn bộ incident input
- insurer / policy validity
- cached RAG context từ Agent 1

Output:

- `is_eligible`
- `description`
- `coverage_summary`
- `citations`

Trạng thái hiện tại:

- đã được nối vào endpoint `GET /claims/{claim_id}/eligibility`
- chưa ép FE phase hiện tại phải đổi flow downstream

## RAG đang dùng theo nguyên tắc nào

- Zilliz là vector backend
- notebook chỉ dùng để tham khảo cách connect/query Zilliz
- không dùng `CATEGORY_KEYWORDS` cho chunking
- chunk policy chỉ có metadata trung tính:
  - `source`
  - `insurer`
  - `article`
  - `chunk_index`
- output agent luôn có `citations` để trace về policy chunk thật

## File chính cần xem

- `backend/app/routers/claims.py`
- `frontend/src/pages/IncidentIntake.tsx`
- `backend/app/agent/models/schemas.py`
- `backend/app/agent/agents/insurance_agents.py`
- `backend/app/agent/rag/retriever.py`
- `backend/app/agent/rag/index_policies.py`
- `backend/app/agent/routers/workflow.py`
- `docs/AI_SERVICES.md`

## Chạy local

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.agent.rag.index_policies
uvicorn app.main:app --reload --port 8000
```

Biến môi trường tối thiểu:

- `OPENAI_API_KEY`
- `HF_TOKEN`
- `ZILLIZ_URI`
- `ZILLIZ_TOKEN`
