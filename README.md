# LotusHacks Website Project

Chào mừng bạn đến với dự án website Hackathon của chúng tôi! Cấu trúc này được thiết kế để tối ưu hóa tốc độ phát triển và sự hợp tác linh hoạt trong môi trường Hackathon.

## 📁 Cấu trúc thư mục (Directory Structure)

```text
LotusHacks/
├── frontend/          # Mã nguồn ứng dụng giao diện người dùng (Next.js/React)
├── backend/           # Mã nguồn máy chủ (Python/FastAPI)
├── shared/            # Các loại (types), hằng số (constants) và tiện ích (utils) dùng chung
├── docs/              # Tài liệu dự án, bài thuyết trình (pitch deck), hình ảnh/video demo
├── scripts/           # Các tập lệnh tiện ích cho xử lý dữ liệu, triển khai (deployment)
├── .gitignore         # Danh sách các tệp và thư mục bị bỏ qua bởi Git
└── README.md          # Tệp hướng dẫn này
```

## 🛠️ Công nghệ đề xuất (Proposed Tech Stack)

- **Frontend:** [Next.js](https://nextjs.org/) (React framework), [Tailwind CSS](https://tailwindcss.com/) (styling), [Lucide Icons](https://lucide.dev/), [Shadcn UI](https://ui.shadcn.com/).
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python), [Uvicorn](https://www.uvicorn.org/) (ASGI server).
- **Database:** [Supabase](https://supabase.com/) (PostgreSQL + Auth + Storage) hoặc [MongoDB](https://www.mongodb.com/).
- **AI/ML (nếu có):** [OpenAI API](https://openai.com/api/), [LangChain](https://www.langchain.com/), [Hugging Face](https://huggingface.co/).
- **Deployment:** [Vercel](https://vercel.com/) (Frontend/Next.js), [Railway](https://railway.app/) (Backend/DB).

## 🚀 Bắt đầu (Getting Started)

1. **Frontend:**
   ```bash
   cd frontend
   npx create-next-app@latest .
   ```

2. **Backend:**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
   *Swagger UI:* `http://localhost:8000/docs`  
   *ReDoc:* `http://localhost:8000/redoc`

3. **Cài đặt các công cụ khác:**
   - Cài đặt [Prisma](https://www.prisma.io/) nếu bạn cần ORM.
   - Cài đặt [Clerk](https://clerk.com/) hoặc [NextAuth.js](https://next-auth.js.org/) cho xác thực người dùng.

## 📝 Ghi chú quan trọng (Important Notes)

- Luôn cập nhật `.gitignore` để không đẩy các tệp chứa thông tin nhạy cảm (`.env`, `node_modules`, `venv`) lên GitHub.
- Tập trung vào MVP (Minimum Viable Product) trước, sau đó mới thêm các tính năng bổ sung.
- Sử dụng các thư viện UI sẵn có để tiết kiệm thời gian thiết kế giao diện.

---
Chúc may mắn với dự án Hackathon của bạn! 🚀
