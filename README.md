# LotusHacks

LotusHacks is a hackathon project focused on AI-assisted vehicle insurance claim intake for the Vietnam market.  
The product helps users report incidents, route claims intelligently, and prepare insurer-specific claim documents.

## Hackathon Goal

Build an end-to-end claim assistant that can:

- Collect incident details in a guided, user-friendly flow
- Use AI triage to decide the next experience (chatbot or assisted mode)
- Provide document checklist support grounded on insurer policy context
- Keep the flow practical for demo-day while preserving production-minded architecture

## Key Features

- 7-step incident intake flow
- AI triage and eligibility checks
- Assisted mode for complex cases
- Chat-based support for eligible/simple cases
- AI-generated checklist guidance and document upload flow
- Claim validation, review, and submission stages
- Admin dashboard for claim operations

## Tech Stack

- Frontend: React + TypeScript + Vite + TanStack Query + Tailwind
- Backend: FastAPI + Motor (MongoDB) + Pydantic
- AI/LLM: OpenAI API
- RAG/Vector DB: Zilliz (Milvus)
- Testing: Pytest (backend), Vitest (frontend)

## Repository Structure

- frontend: React web app and user/admin pages
- backend: FastAPI APIs, agent logic, claim workflows, tests
- backend/app/agent: triage + coverage + checklist + RAG integration
- database: local Mongo init assets
- docs: pitch and AI service notes
- shared: shared project types/assets

## High-Level Flow

1. User creates or resumes a draft claim.
2. User completes 7-step incident intake.
3. Backend triage agent evaluates case complexity.
4. Routing:
   - Complex case -> Assisted Mode
   - Non-complex case -> Eligibility pre-check
5. If eligible, user can continue with chat/checklist + document upload.

## Environment Setup

### 1. Create environment file

At repository root:

```bash
cp .env.example .env
```

Important variables to set:

- OPENAI_API_KEY
- ZILLIZ_URI
- ZILLIZ_TOKEN
- MONGODB_URI
- MONGODB_DB_NAME
- JWT_SECRET

## Backend Setup

The team preference for this repo is using conda instead of a .venv.

```bash
conda create -n lotushacks-api python=3.11 -y
conda activate lotushacks-api
pip install -r requirements.txt
```

Run backend:

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Health check:

- GET http://localhost:8000/health

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Default local URL:

- http://localhost:5173

## Optional: Index Policy Data to Zilliz

```bash
cd backend
python -m app.agent.rag.index_policies
```

## Test Commands

Backend tests:

```bash
cd backend
pytest -q
```

Backend agent-focused tests:

```bash
cd backend
pytest tests/test_agent -q
```

Frontend tests/build:

```bash
cd frontend
npm run test
npm run build
```

## API Surface (Core)

- Auth: sign-in/sign-up/google
- Claims: create, patch, triage, eligibility, documents, validation, submit
- Chat: session management, message processing, AI response
- Uploads: claim document upload endpoints
- Admin: claim status management and oversight

## Notes For Judges and Mentors

- This repository is actively iterated during LotusHacks.
- Some modules are demo-optimized while preserving scalable architecture boundaries.
- AI routing and checklist generation are designed to be explainable and policy-grounded.

## Team Members

The project is built by Team LotusHacks:

| Member | Role |
| --- | --- |
| Đinh Việt Phát | Project Manager & AI Developer |
| Nguyễn Võ Ngọc Bảo | Fullstack Developer |
| Bùi Nhật Anh Khôi | AI/ML Developer |
| Phan Quốc Đại Sơn | AI/ML Developer |

## Related Docs

- AI_SERVICES.md
- docs/AI_SERVICES.md
- docs/PITCH.md
