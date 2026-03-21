from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel, Field
from .schemas import ImageAnalysis

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


ALLOWED_PARTS = [
    "front_bumper",
    "rear_bumper",
    "left_headlight",
    "right_headlight",
    "hood",
    "windshield",
    "left_door",
    "right_door",
    "left_mirror",
    "right_mirror",
    "rear_body",
    "unknown_damage",
]


class OpenAIVisionOutput(BaseModel):
    vehicle_present: bool = False
    vehicle_type: str = "unknown"   # car | motorcycle | truck | bus | unknown
    is_damage_visible: bool = False
    damaged_parts: List[str] = Field(default_factory=list)
    severity: str = "uncertain"     # none | minor | moderate | severe | uncertain
    confidence: float = 0.0
    short_reason: str = ""


class ImageAnalyzer:
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

    def analyze(self, image_path: str) -> ImageAnalysis:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy ảnh: {image_path}")

        if OpenAI is None:
            return ImageAnalysis(
                image_path=str(path),
                ran_model=False,
                model_name=self.model_name,
                notes=[
                    "Chưa cài package openai.",
                    "Hãy chạy: pip install openai",
                ],
            )

        if self.client is None:
            return ImageAnalysis(
                image_path=str(path),
                ran_model=False,
                model_name=self.model_name,
                notes=[
                    "Chưa có OPENAI_API_KEY.",
                    "Hãy set OPENAI_API_KEY rồi chạy lại.",
                ],
            )

        prompt = f"""
Bạn là bộ phân tích ảnh tổn thất xe cho bảo hiểm.

Nhiệm vụ:
1. Xác định trong ảnh có phương tiện hay không.
2. Nếu có, xác định loại phương tiện chính: car, motorcycle, truck, bus, unknown.
3. Chỉ đánh giá phần hư hỏng NHÌN THẤY RÕ.
4. damaged_parts chỉ được chọn từ danh sách:
{", ".join(ALLOWED_PARTS)}
5. Nếu không chắc, không đoán. Khi đó:
   - is_damage_visible = false hoặc
   - damaged_parts = []
   - severity = "uncertain"
6. confidence là số từ 0 đến 1.
7. short_reason viết rất ngắn, 1 câu.
8. Chỉ trả về JSON hợp lệ, không thêm markdown, không thêm giải thích ngoài JSON.

Schema JSON bắt buộc:
{{
  "vehicle_present": true,
  "vehicle_type": "car",
  "is_damage_visible": true,
  "damaged_parts": ["front_bumper", "left_headlight"],
  "severity": "moderate",
  "confidence": 0.83,
  "short_reason": "Phần đầu xe có hư hỏng nhìn thấy được."
}}
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
            parsed = OpenAIVisionOutput.model_validate(parsed_dict)

            vehicle_labels = []
            if parsed.vehicle_present and parsed.vehicle_type != "unknown":
                vehicle_labels.append(parsed.vehicle_type)

            return ImageAnalysis(
                image_path=str(path),
                ran_model=True,
                model_name=self.model_name,
                vehicle_present=parsed.vehicle_present,
                vehicle_type=parsed.vehicle_type,
                is_damage_visible=parsed.is_damage_visible,
                damaged_parts=parsed.damaged_parts,
                severity=parsed.severity,
                confidence=parsed.confidence,
                accident_scene_label="possible_vehicle_accident" if parsed.vehicle_present else "no_vehicle_detected",
                accident_scene_confidence=parsed.confidence,
                vehicle_labels=vehicle_labels,
                detections=[],
                crop_path=None,
                notes=[parsed.short_reason] if parsed.short_reason else [],
            )

        except Exception as e:
            return ImageAnalysis(
                image_path=str(path),
                ran_model=False,
                model_name=self.model_name,
                notes=[f"Lỗi khi gọi OpenAI Vision: {e}"],
            )