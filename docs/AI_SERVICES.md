# LotusHacks AI Services

Tài liệu này mô tả lại workflow AI/RAG theo đúng mục tiêu giai đoạn hiện tại:

- chỉ build đoạn `E2 -> E3 -> F -> H -> H1 -> J/END1`
- tập trung vào 2 agent
- dùng Zilliz làm vector backend
- chưa mở rộng sang OCR/import policy, dossier builder, submission router hay tracking

## 0. Cách workflow này được gắn vào main hiện tại

Code mới từ `main` đã có sẵn:

- `StartClaim` để lấy vehicle/policy thật
- `IncidentIntake` để thu 7 bước và patch incident vào claim
- `claims/{claim_id}/triage` để FE lấy decision cuối step 7

Branch này tích hợp workflow agent theo nguyên tắc:

1. Không thay schema 7 bước hiện có của FE/BE
2. Không route bằng câu trả lời thủ công ở step 7 nữa
3. Lấy toàn bộ dữ liệu incident đã lưu trong claim
4. Map claim đó sang `IncidentInput` của agent
5. Dùng decision thật của Agent 1 để route:
   - `assisted_mode = true` -> `/assisted-mode`
   - `assisted_mode = false` -> `/chat`

Như vậy phase hiện tại chỉ thay `decision engine`, không đụng downstream pages của `main`.

## 1. Mục tiêu giai đoạn hiện tại

### 1.1. Agent 1

Agent 1 là `Policy + Rule Engine / Triage Agent`.

Nhiệm vụ:

- nhận mô tả sự cố từ user
- retrieve policy/legal context liên quan bằng RAG
- đối chiếu input user với policy context
- classifier case thành:
  - `COMPLEX`
  - `NOT_COMPLEX`
- giải thích vì sao phân loại như vậy

Output:

```json
{
  "is_complex": true,
  "description": "...",
  "triggered_rules": ["..."],
  "citations": [
    {
      "source": "policy_pti.txt",
      "article": "Điều 7",
      "chunk_id": "..."
    }
  ]
}
```

### 1.2. Agent 2

Agent 2 là `Coverage Pre-check Agent`.

Nhiệm vụ:

- nhận lại input của user
- nhận thêm cached RAG context từ Agent 1
- retrieve thêm policy theo insurer / policy linked
- kiểm tra:
  - hiệu lực policy
  - phạm vi bảo hiểm
  - quyền lợi
  - loại trừ
  - miễn thường / khấu trừ
- classifier thành:
  - `ELIGIBLE`
  - `NOT_ELIGIBLE`

Output:

```json
{
  "is_eligible": false,
  "description": "...",
  "coverage_summary": "...",
  "citations": [
    {
      "source": "policy_baoviet.txt",
      "article": "Điều 4",
      "chunk_id": "..."
    }
  ]
}
```

## 2. Đánh giá flow hiện tại của bạn

Flow bạn thiết kế cho giai đoạn này là hợp lý với use case bảo hiểm ô tô Việt Nam.

Điểm tốt:

- chia rõ `triage` và `coverage pre-check` thành 2 quyết định nghiệp vụ khác nhau
- tách nhánh `Assisted Mode` ra sớm, phù hợp các case có thương tích / bên thứ ba / hiện trường phức tạp
- giữ `Dynamic Checklist` ở sau coverage pre-check, đúng logic claim
- chưa ôm cả OCR/submission/tracking ngay từ đầu, giúp phase 1 khả thi hơn

Điểm cần làm rõ để tránh lệch implementation:

- `xe còn chạy được không` là input quan trọng, nhưng không nên tự động đồng nghĩa với `COMPLEX`
- `vụ việc phức tạp` nên được hiểu là:
  - có thương tích
  - có bên thứ ba
  - có hiện trường cao tốc / nhiều xe / liên hoàn
  - có tình huống cần hotline / giữ hiện trường / phối hợp ngay
- Agent 2 phải có bước `policy validity` riêng; nếu không sẽ mới chỉ là exclusion checker chứ chưa phải coverage pre-check đầy đủ
- checklist ở giai đoạn này nên gọi là `dynamic checklist sơ bộ`, chưa cần pretend là full dossier workflow

## 3. Hiện trạng code so với requirement

### 3.1. Các điểm hiện đã khớp hơn

- có 2 agent tách biệt:
  - Agent 1 phân loại `complex / not complex`
  - Agent 2 phân loại `eligible / not eligible`
- dữ liệu đầu vào cho agent hiện đi từ claim thật của `main`, không còn dựa vào dummy payload khi user submit FE
- `IncidentIntake` của FE đã route theo `claims.triage` response thay vì nhìn trực tiếp vào answer của step 7
- có `citations` trong output của cả 2 agent
- đã chuyển vector backend sang Zilliz
- đã bỏ `CATEGORY_KEYWORDS` khỏi chunking/index
- RAG không còn filter theo `triage_rules / coverage_rules`
- Agent 2 đã có thêm bước `policy validity pre-check`
- dummy data đã được mở rộng thêm field và nhiều case hơn

### 3.2. Các điểm vẫn là gap / technical debt

1. Cache giữa Agent 1 -> Agent 2 vẫn là in-memory dictionary.
   Nên thay bằng Redis nếu muốn multi-worker / production-safe.

2. Corpus hiện mới là `policy_*.txt`.
   Chưa có ingestion từ PDF/OCR/legal corpus thực tế.

3. Checklist theo insurer mới ở mức generic.
   Chưa map sâu theo biểu mẫu riêng từng doanh nghiệp bảo hiểm.

4. Router đang sinh checklist ngay trong API layer.
   Về sau nên tách sang `ChecklistService` riêng.

5. Coverage decision hiện vẫn dựa nhiều vào LLM sau bước pre-check.
   Về sau nên tăng rule layer cho các exclusion/validity chắc chắn.

6. Adapter từ claim của `main` mới chỉ dùng các field đang có sẵn ở 7 bước.
   Những field giàu hơn như `driver_license_valid`, `alcohol_involved`, `damage_parts`
   vẫn cần được bổ sung ở phase sau nếu muốn Agent 2 mạnh đúng như thiết kế ban đầu.

## 4. Thiết kế agent nên build cho phase hiện tại

## 4.1. Agent 1 - Triage Agent

### Input nên có

Required:

- `time`
- `location`
- `description`
- `third_party_involved`
- `vehicle_drivable`
- `injuries`

Recommended thêm:

- `gps_coordinates`
- `incident_type`
- `highway_incident`
- `number_of_vehicles_involved`
- `estimated_damage`
- `weather_condition`
- `road_condition`
- `towing_required`
- `photos_taken`
- `police_report`
- `insurer` nếu đã linked policy

### Process đề xuất

1. Chuẩn hóa input:
   - normalize time
   - normalize location/GPS
   - normalize incident_type
   - build narrative summary cho query

2. Rule-based fast path:
   - `injuries=True` -> complex
   - `third_party_involved=True` -> complex
   - `highway_incident=True` -> complex
   - `number_of_vehicles_involved>=3` -> complex
   - mô tả có tín hiệu rõ kiểu `liên hoàn`, `cháy`, `kẹt người` -> complex

3. Nếu chưa đủ chắc chắn:
   - query RAG bằng semantic query trên policy/legal corpus
   - nếu có insurer linked thì ưu tiên filter theo insurer; nếu không thì search toàn corpus

4. LLM/classifier:
   - nhận input chuẩn hóa + policy context + citations
   - trả về `is_complex` và `description`

5. Cache:
   - lưu summary query
   - lưu retrieved context
   - lưu citations
   - lưu session/workflow id

### Output

- `is_complex`
- `description`
- `triggered_rules`
- `citations`

### Routing

- `true` -> `Assisted Mode`
- `false` -> `Agent 2`

## 4.2. Agent 2 - Coverage Pre-check Agent

### Input nên có

- toàn bộ input của Agent 1
- `policy_id`
- `insurer`
- `policy_active`
- `policy_start_date`
- `policy_end_date`
- `driver_license_valid`
- `vehicle_registration_valid`
- `alcohol_involved`
- `damage_parts`
- `theft_scope`
- cached RAG context từ Agent 1

### Process đề xuất

1. Policy validity pre-check:
   - `policy_active=False` -> not eligible
   - incident time nằm ngoài thời hạn policy -> not eligible

2. Exclusion fast path:
   - `alcohol_involved=True` -> not eligible
   - `driver_license_valid=False` -> not eligible
   - `vehicle_registration_valid=False` -> not eligible

3. Nếu chưa conclude:
   - load cached context từ Agent 1
   - query thêm policy theo insurer
   - query bổ sung coverage / exclusion / deductible theo semantic query

4. LLM/classifier:
   - đối chiếu `coverage`, `exclusion`, `deductible`, `policy validity`
   - trả `is_eligible`, `description`, `coverage_summary`

5. Routing:
   - `true` -> `Dynamic Checklist`
   - `false` -> `NOT_ELIGIBLE -> END1`

## 5. RAG nên build thế nào cho 2 agent

## 5.1. Nguyên tắc quan trọng

- Zilliz chỉ là nơi lưu vector + metadata.
- Notebook dùng để học cách connect/query Zilliz, không dùng để định nghĩa nghiệp vụ RAG.
- Không nên gắn `category` vào chunk bằng keyword rồi lấy đó làm logic chính cho agent.
- Agent phải dựa trên policy chunk thật và `citation` thật.

## 5.2. Ingestion workflow cho RAG

### Bước 1. Source collection

Nguồn tài liệu nên có:

- policy theo từng insurer
- quy tắc, điều khoản, phụ lục
- văn bản hướng dẫn hồ sơ bồi thường
- văn bản pháp lý nền nếu bạn muốn cross-check later

### Bước 2. Text extraction

Phase hiện tại:

- dùng `.txt` curated bằng tay là ổn

Phase sau:

- parser PDF
- OCR cho scan xấu
- giữ layout metadata: heading / article / appendix / page

### Bước 3. Chunking

Nên chunk theo cấu trúc tài liệu:

- ưu tiên paragraph / article boundary
- overlap nhẹ để giữ ngữ cảnh
- tránh chunk theo keyword taxonomy

Recommended metadata:

```json
{
  "source": "policy_pti.txt",
  "insurer": "PTI",
  "article": "Điều 7",
  "chunk_index": 12
}
```

Phase sau có thể thêm:

- `document_type`
- `policy_version`
- `effective_from`
- `effective_to`
- `page_number`
- `section_title`

### Bước 4. Embedding + indexing

- embed tiếng Việt bằng multilingual sentence-transformers trước
- upsert vào Zilliz với stable chunk id
- giữ idempotent re-index

## 5.3. Online RAG workflow cho Agent 1

### Query building

Build từ:

- incident type
- description
- injuries
- third party
- highway
- number of vehicles
- towing
- location / GPS

### Retrieval strategy

Phase hiện tại:

1. semantic search top-k trên corpus
2. nếu có insurer linked thì ưu tiên filter theo insurer
3. trả context + citations

Phase sau:

1. query rewriting
2. hybrid retrieval:
   - dense search
   - BM25 / keyword search
3. reranker
4. context compression

### Lý do tách riêng Agent 1 RAG

Agent 1 không cần toàn bộ detail claim. Nó chỉ cần đủ context để trả lời:

- case có cần Assisted Mode không
- vì sao
- nên cảnh báo khẩn cấp gì

## 5.4. Online RAG workflow cho Agent 2

### Query building

Build từ:

- description
- incident_type
- insurer
- policy validity fields
- alcohol / GPLX / đăng kiểm
- damage_parts
- theft_scope

### Retrieval strategy

Phase hiện tại:

1. load cached triage context
2. retrieve thêm insurer-specific chunks
3. merge context
4. LLM evaluate

Phase sau:

1. multi-query retrieval:
   - policy validity query
   - coverage scope query
   - exclusion query
   - deductible query
2. rerank từng nhóm
3. combine final context cho Agent 2

### Vì sao Agent 2 cần RAG riêng

Agent 2 khác Agent 1 ở chỗ nó phải trả lời câu hỏi cụ thể hơn:

- policy còn hiệu lực không
- sự cố có nằm trong phạm vi bảo hiểm không
- có exclusion nào kích hoạt không
- có deductible/mức miễn thường nào cần chú ý không

## 5.5. Citation / traceability

Mỗi output nên luôn có:

- `source`
- `article`
- `chunk_id`
- optional `score`

Mục tiêu:

- audit được agent đã dựa vào chunk nào
- tránh câu trả lời “nghe hợp lý nhưng không trace được”
- cho phép QA/reviewer kiểm tra lại nhanh

## 5.6. Roadmap RAG nâng cao

Khi đi sang phase 2/3, nên nâng cấp theo thứ tự này:

1. PDF parser + OCR ingestion
2. metadata giàu hơn (`section_title`, `page_number`, `policy_version`)
3. Redis cache cho retrieval/session
4. hybrid retrieval
5. reranker
6. evaluation set cho từng insurer
7. retrieval observability / tracing

## 6. Tech stack nên dùng

## 6.1. Runtime core

- API / orchestration: `FastAPI`
- schema: `Pydantic`
- vector DB: `Zilliz`
- embeddings: `sentence-transformers`
- primary LLM: `OpenAI`
- fallback LLM: `Qwen`
- cache/session: `Redis`
- app data / workflow state: `MongoDB` ở phase hiện tại

## 6.2. Tool mapping theo use case của bạn

### OpenAI API

Nên dùng cho:

- structured classification cho 2 agent
- explanation generation có citation
- sau này dùng cho checklist generation

### Qwen

Nên dùng cho:

- fallback runtime
- batch testing rẻ hơn
- regression run nếu muốn giảm cost

### Manus

Nên dùng cho:

- research/prototyping ngoài runtime
- chuẩn hóa tài liệu policy
- trợ giúp build quy trình OCR/legal ingestion

Không nên là thành phần bắt buộc trong critical runtime path của agent.

### ByteRover

Nên dùng cho:

- hỗ trợ dev/research trong VS Code
- tìm pattern code, test coverage, refactor

Không phải thành phần runtime của workflow claim.

### BrightData

Nên dùng cho:

- thu thập public policy docs / điều khoản công khai nếu cần monitoring
- update corpus từ nguồn public ở phase sau

Không nên đưa trực tiếp vào online request path của user.

### Dify

Phù hợp nếu bạn muốn:

- có UI để prompt test nhanh
- dựng flow demo nhanh cho product/business
- A/B prompt / flow mà không phải sửa code nhiều

Nếu team đang build hoàn toàn trong VS Code/FastAPI thì Dify là optional, không bắt buộc.

### Exa

Nên dùng cho:

- external knowledge retrieval
- nghiên cứu legal/policy cập nhật
- tìm nguồn tài liệu khi mở rộng corpus

Không phải tool nên gọi trực tiếp cho mỗi request claim runtime.

## 6.3. Stack khuyến nghị theo phase

### Phase 1 - đúng scope hiện tại

- FastAPI
- Pydantic
- OpenAI + Qwen
- Zilliz
- sentence-transformers
- MongoDB
- Redis

### Phase 2 - tăng chất lượng RAG

- hybrid search
- reranker
- parser PDF/OCR
- evaluation dataset

### Phase 3 - mở rộng workflow

- object storage cho file ảnh/pdf
- background job queue
- OCR service
- submission connectors
- workflow state machine

## 7. Các trường input nên bổ sung

Ngoài 6 trường core ban đầu, phase này nên có thêm:

- `gps_coordinates`
- `incident_type`
- `policy_id`
- `insurer`
- `policy_active`
- `policy_start_date`
- `policy_end_date`
- `driver_license_valid`
- `vehicle_registration_valid`
- `alcohol_involved`
- `highway_incident`
- `number_of_vehicles_involved`
- `estimated_damage`
- `damage_parts`
- `weather_condition`
- `road_condition`
- `towing_required`
- `theft_scope`
- `photos_taken`
- `police_report`

Những field này đủ để:

- triage tốt hơn
- coverage pre-check đầy đủ hơn
- chuẩn bị cho checklist phase sau

## 8. Dummy data nên build ra sao

## 8.1. Nhóm case tối thiểu phải có

- liên hoàn trên cao tốc, có thương tích
- va chạm đơn giản, không bên thứ ba
- ngập nước / thủy kích
- vỡ kính
- mất cắp bộ phận
- mất cắp toàn bộ xe
- exclusion do nồng độ cồn
- exclusion do GPLX/đăng kiểm
- policy hết hiệu lực
- tự đâm vào vật cản, không bên thứ ba

## 8.2. Hiện đã thêm vào dataset

File:

- `backend/app/agent/data/dummy_incidents.json`

Dataset hiện có:

- case `COMPLEX`
- case `SIMPLE -> ELIGIBLE`
- case `SIMPLE -> NOT_ELIGIBLE`
- case `policy expired`
- case `theft_scope=toan_bo`

## 8.3. Cách dùng dummy data

Nên dùng 3 lớp:

1. `unit fixtures`
   - test logic agent riêng

2. `workflow fixtures`
   - test API end-to-end

3. `evaluation fixtures`
   - đo đúng/sai của triage và coverage theo expected labels

## 9. Kết luận kỹ thuật

Nếu bám đúng phase hiện tại, giải pháp nên là:

1. giữ 2 agent như hiện nay
2. giữ Zilliz làm vector backend
3. không dùng `CATEGORY_KEYWORDS` cho policy chunking
4. để RAG làm nhiệm vụ retrieve + citation
5. để Agent 1 quyết định `complex/not complex`
6. để Agent 2 quyết định `eligible/not eligible`
7. dùng Redis thay in-memory cache ở bước tiếp theo

Đây là hướng cân bằng giữa:

- đủ sát nghiệp vụ bảo hiểm
- đủ gọn để build trong VS Code phase đầu
- không over-engineer quá sớm
