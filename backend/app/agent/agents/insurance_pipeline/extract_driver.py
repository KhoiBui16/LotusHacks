from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel
from .schemas import ImageAnalysis  # có thể bỏ nếu bạn không dùng

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


class DriverLicenseOutput(BaseModel):
    ran_model: bool = True
    model_name: str = "unknown"

    document_type: str = "unknown"   # driver_license | unknown
    is_driver_license: bool = False

    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    license_number: Optional[str] = None
    license_class: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None

    confidence: float = 0.0
    short_reason: str = ""
    notes: list[str] = []


class DriverLicenseAnalyzer:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("OPENAI_VISION_MODEL", "gpt-5.4-mini")
        self.client = OpenAI(api_key=self.api_key) if (OpenAI and self.api_key) else None

    def _image_to_data_url(self, image_path: Path) -> str:
        mime_type, _ = mimetypes.guess_type(str(image_path))
        if mime_type is None:
            mime_type = "image/jpeg"

        with image_path.open("rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        return f"data:{mime_type};base64,{b64}"

    def _extract_json_text(self, raw_text: str) -> str:
        text = raw_text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            lines = text.splitlines()
            if lines and lines[0].lower().startswith("json"):
                lines = lines[1:]
            text = "\n".join(lines).strip()
        return text

    def analyze(self, image_path: str) -> DriverLicenseOutput | dict:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy ảnh: {image_path}")

        if OpenAI is None:
            return {
                "ran_model": False,
                "model_name": self.model_name,
                "notes": [
                    "Chưa cài package openai.",
                    "Hãy chạy: pip install openai",
                ],
            }

        if self.client is None:
            return {
                "ran_model": False,
                "model_name": self.model_name,
                "notes": [
                    "Chưa có OPENAI_API_KEY.",
                    "Hãy set OPENAI_API_KEY rồi chạy lại.",
                ],
            }

        prompt = """
Bạn là bộ phân tích ảnh giấy phép lái xe cho bài toán bảo hiểm.

Nhiệm vụ:
1. Xác định ảnh có phải là giấy phép lái xe hay không.
2. Nếu đúng là giấy phép lái xe, trích xuất các trường nếu nhìn thấy rõ:
   - full_name
   - date_of_birth
   - license_number
   - license_class
   - issue_date
   - expiry_date
3. Nếu không chắc, không đoán bừa.
4. confidence là số từ 0 đến 1.
5. short_reason viết rất ngắn, 1 câu.
6. Chỉ trả về JSON hợp lệ, không thêm markdown, không thêm giải thích ngoài JSON.

Schema JSON bắt buộc:
{
  "document_type": "driver_license",
  "is_driver_license": true,
  "full_name": "Nguyen Van A",
  "date_of_birth": "1999-01-01",
  "license_number": "123456789",
  "license_class": "B2",
  "issue_date": "2023-01-10",
  "expiry_date": "2033-01-10",
  "confidence": 0.93,
  "short_reason": "Anh la giay phep lai xe va doc duoc thong tin chinh."
}
"""

        data_url = self._image_to_data_url(path)

        try:
            response = self.client.responses.create(
                model=self.model_name,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {
                                "type": "input_image",
                                "image_url": data_url,
                                "detail": "high",
                            },
                        ],
                    }
                ],
            )

            raw_text = response.output_text
            json_text = self._extract_json_text(raw_text)
            parsed_dict = json.loads(json_text)
            parsed = DriverLicenseOutput.model_validate(parsed_dict)

            return parsed

        except Exception as e:
            return {
                "ran_model": False,
                "model_name": self.model_name,
                "notes": [f"Lỗi khi gọi OpenAI Vision: {e}"],
            }