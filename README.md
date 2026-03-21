# LotusHacks

Repo này đang được tích hợp theo hướng:

- FE `Start Claim` và `Incident Intake` lấy dữ liệu thật từ `main`
- workflow agent dùng dữ liệu 7 bước hiện có để quyết định `assisted_mode = yes/no`
- downstream hiện tại của `main` được giữ nguyên:
  - `assisted_mode = true` -> `/assisted-mode`
  - `assisted_mode = false` -> `/chat`

Phase hiện tại chưa mở rộng sang OCR/import policy tự động, dossier builder, submission router hay claim tracking đầy đủ.

## Kiến trúc hiện tại

### FE

- `frontend/src/pages/StartClaim.tsx`
  - lấy vehicle/policy thật
  - tạo draft claim
  - chuyển vào `IncidentIntake`
- `frontend/src/pages/IncidentIntake.tsx`
  - thu 7 bước input
  - patch incident vào claim hiện tại
  - gọi `POST /claims/{claim_id}/triage`
  - route theo decision thật từ workflow agent

### BE

- `backend/app/routers/claims.py`
  - nhận dữ liệu claim hiện có của `main`
  - map sang `AgentIncidentInput`
  - gọi Agent 1 để trả decision `assisted_mode`
  - giữ nguyên contract response hiện có của `main`
- `backend/app/agent/routers/workflow.py`
  - router workflow 2 agent đầy đủ
  - mount tại `/api/v1/agent/workflow`
- `backend/app/agent/rag`
  - index/retrieve policy context trên Zilliz

## Workflow phase này

### Agent 1

Input lấy từ 7 bước hiện có:

- `incident type`
- `date`
- `time`
- `location_text`
- `description`
- `has_third_party`
- `can_drive`
- `needs_towing`
- `has_injury`

Input được làm giàu thêm từ vehicle/claim linked:

- `insurer`
- `policy_id`
- `effective_date`
- `expiry`
- `plate`
- `model`

Output:

- `assisted_mode = true` nếu case được phân loại phức tạp
- `assisted_mode = false` nếu case có thể đi tiếp flow thường

### Agent 2

Đã có trong BE để dùng cho coverage pre-check phase sau:

- policy validity
- insurer-specific retrieval
- exclusion / deductible / eligibility pre-check

FE hiện tại của `main` chưa buộc phải dùng Agent 2 để đổi route, nên downstream chưa bị đụng.

## RAG

Nguyên tắc đang dùng:

- Zilliz là vector backend
- notebook chỉ dùng để tham khảo cách connect/query Zilliz
- không dùng keyword taxonomy kiểu `CATEGORY_KEYWORDS` để gán chunk nghiệp vụ
- chunk policy chỉ giữ metadata trung tính:
  - `source`
  - `insurer`
  - `article`
  - `chunk_index`

Tài liệu policy mẫu hiện nằm ở:

- `backend/app/agent/data/policy_baoviet.txt`
- `backend/app/agent/data/policy_mic.txt`
- `backend/app/agent/data/policy_pti.txt`

## Local setup

### 1. Backend env

Sao chép:

```powershell
Copy-Item backend\.env.example backend\.env
```

Các biến tối thiểu cần có:

- `OPENAI_API_KEY`
- `HF_TOKEN`
- `ZILLIZ_URI`
- `ZILLIZ_TOKEN`

Bạn cũng có thể cấu hình Zilliz qua:

- `MILVUS_HOST`
- `MILVUS_PORT`

### 2. Backend install

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Index policy lên Zilliz

```powershell
cd backend
.\venv\Scripts\python.exe -m app.agent.rag.index_policies
```

### 4. Chạy backend

```powershell
cd backend
.\venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

### 5. Chạy frontend

```powershell
cd frontend
npm install
npm run dev
```

## Test

Backend:

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_agent -q
```

Frontend smoke check:

```powershell
cd frontend
npm run build
```

## Tài liệu thêm

- `AI_SERVICES.md`
- `docs/AI_SERVICES.md`
