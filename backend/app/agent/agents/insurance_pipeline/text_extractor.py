from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .schemas import ClaimInfo, ParsedDocument, PolicyInfo


ATTACHMENT_KEYWORDS = {
    "claim_form": ["đơn yêu cầu bồi thường", "đơn yêu cầu"],
    "driver_license": ["giấy phép lái xe", "gplx"],
    "vehicle_registration": ["đăng ký xe", "cà vẹt xe"],
    "damage_photos": ["ảnh hiện trường", "ảnh tổn thất", "hình ảnh tổn thất"],
    "police_report": ["biên bản công an", "biên bản hiện trường"],
    "statement": ["bản tường trình", "tường trình sự việc"],
}


class ClaimExtractor:
    def extract(self, file_name: str, file_type: str, cleaned_text: str, num_chars: int) -> ParsedDocument:
        policy = self._extract_policy(cleaned_text)
        claim = self._extract_claim(cleaned_text)

        return ParsedDocument(
            file_name=file_name,
            file_type=file_type,
            num_chars=num_chars,
            cleaned_text=cleaned_text,
            policy=policy,
            claim=claim,
        )

    def _extract_policy(self, text: str) -> PolicyInfo:
        insurer = self._search(r"Công ty bảo hiểm\s*\|\s*(.+)", text)
        policy_number = self._search(r"Số hợp đồng\s*\|\s*(.+)", text)
        claimant_name = self._search(r"Chủ xe được bảo hiểm\s*\|\s*(.+)", text)
        plate_number = self._search(r"Biển số xe\s*\|\s*([A-Z0-9\.\-]+)", text)

        coverage_line = self._search(r"Hiệu lực bảo hiểm\s*\|\s*(.+)", text)
        coverage_start = None
        coverage_end = None
        if coverage_line:
            m = re.search(r"Từ\s*(\d{2}/\d{2}/\d{4})\s*đến\s*(\d{2}/\d{2}/\d{4})", coverage_line, re.IGNORECASE)
            if m:
                coverage_start = m.group(1)
                coverage_end = m.group(2)

        vehicle_type = self._infer_vehicle_type(text.lower())

        return PolicyInfo(
            policy_number=policy_number,
            insurer=insurer,
            claimant_name=claimant_name,
            vehicle_type=vehicle_type,
            plate_number=plate_number,
            coverage_start=coverage_start,
            coverage_end=coverage_end,
        )

    def _extract_claim(self, text: str) -> ClaimInfo:
        lower_text = text.lower()

        incident_type_raw = self._search(r"Loại sự kiện:\s*(.+)", text)
        incident_time = self._search(r"Thời gian xảy ra tai nạn:\s*(.+)", text)
        incident_location = self._search(r"Địa điểm:\s*(.+)", text)
        narrative = self._search(r"Diễn biến:\s*(.+)", text)

        claimed_damage = self._extract_damage_items(lower_text)
        attachments_listed = self._extract_attachments(lower_text)
        driver_has_license = self._infer_license(lower_text)

        incident_type = "unknown"
        if incident_type_raw:
            it = incident_type_raw.lower()
            if any(k in it for k in ["tai nạn", "va chạm", "đâm", "tông"]):
                incident_type = "vehicle_accident"
            elif any(k in it for k in ["trộm", "mất cắp", "theft"]):
                incident_type = "theft"
            elif any(k in it for k in ["cháy", "hỏa hoạn", "fire"]):
                incident_type = "fire"

        return ClaimInfo(
            incident_type=incident_type,
            incident_time=incident_time,
            incident_location=incident_location,
            claimed_damage=claimed_damage,
            narrative=narrative,
            driver_has_license=driver_has_license,
            attachments_listed=attachments_listed,
        )

    def _search(self, pattern: str, text: str, flags=re.IGNORECASE) -> Optional[str]:
        m = re.search(pattern, text, flags)
        return m.group(1).strip() if m else None

    def _infer_vehicle_type(self, lower_text: str) -> Optional[str]:
        if "ô tô" in lower_text or "xe hơi" in lower_text or "car" in lower_text:
            return "car"
        if "xe máy" in lower_text or "motorbike" in lower_text or "motorcycle" in lower_text:
            return "motorcycle"
        if "xe tải" in lower_text or "truck" in lower_text:
            return "truck"
        return None

    def _extract_damage_items(self, lower_text: str) -> List[str]:
        ordered_mapping = [
            ("cản trước bên trái", "front_left_bumper"),
            ("cản trước bên phải", "front_right_bumper"),
            ("đèn pha bên trái", "left_headlight"),
            ("đèn trước trái", "left_headlight"),
            ("đèn pha bên phải", "right_headlight"),
            ("nắp capo", "hood"),
            ("cửa trái", "left_door"),
            ("cửa phải", "right_door"),
            ("gương trái", "left_mirror"),
            ("gương phải", "right_mirror"),
            ("cản sau", "rear_bumper"),
            ("đuôi xe", "rear_body"),
            ("cản trước", "front_bumper"),
        ]

        found = []

        for vn, norm in ordered_mapping:
            if vn in lower_text:
                # tránh thêm front_bumper nếu đã có front_left/right_bumper
                if norm == "front_bumper" and (
                    "front_left_bumper" in found or "front_right_bumper" in found
                ):
                    continue
                if norm not in found:
                    found.append(norm)

        return found

    def _extract_attachments(self, lower_text: str) -> List[str]:
        found = []
        for canonical, patterns in ATTACHMENT_KEYWORDS.items():
            if any(p in lower_text for p in patterns):
                found.append(canonical)
        return found

    def _infer_license(self, lower_text: str) -> Optional[bool]:
        if "không có gplx" in lower_text or "không có giấy phép lái xe" in lower_text:
            return False
        if (
            "giấy phép lái xe" in lower_text
            or "gplx hợp lệ" in lower_text
            or "bản sao giấy phép lái xe" in lower_text
        ):
            return True
        return None


def extract_claim_info(cleaned_text: str) -> Dict[str, Any]:
    parsed = ClaimExtractor().extract(
        file_name="sample",
        file_type=".docx",
        cleaned_text=cleaned_text,
        num_chars=len(cleaned_text),
    )

    return {
        "insurer": parsed.policy.insurer,
        "policy_number": parsed.policy.policy_number,
        "policyholder_name": parsed.policy.claimant_name,
        "plate_number": parsed.policy.plate_number,
        "vehicle_type": parsed.policy.vehicle_type,
        "incident_type": parsed.claim.incident_type,
        "incident_time": parsed.claim.incident_time,
        "incident_location": parsed.claim.incident_location,
        "driver_name": None,
        "claim_description": parsed.claim.narrative,
        "claimed_damage": parsed.claim.claimed_damage,
    }