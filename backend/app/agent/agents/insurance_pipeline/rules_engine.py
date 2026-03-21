from __future__ import annotations

from typing import List, Tuple, Optional
from datetime import date, datetime
from typing import List, Tuple
from .schemas import ParsedDocument, ImageAnalysis, VerificationResult


DAMAGE_EQUIVALENTS = {
    "front_left_bumper": {"front_left_bumper", "front_bumper"},
    "front_bumper": {"front_bumper", "front_left_bumper", "front_right_bumper"},
    "left_headlight": {"left_headlight"},
    "right_headlight": {"right_headlight"},
    "hood": {"hood", "bonnet"},
    "rear_bumper": {"rear_bumper"},
    "rear_body": {"rear_body"},
    "left_door": {"left_door"},
    "right_door": {"right_door"},
    "left_mirror": {"left_mirror"},
    "right_mirror": {"right_mirror"},
    "windshield": {"windshield", "front_glass"},
}

# map vehicle type -> accepted license classes
VEHICLE_LICENSE_COMPATIBILITY = {
    "motorbike": {"A1", "A", "A2"},
    "motorcycle": {"A1", "A", "A2"},
    "car": {"B1", "B", "B2", "C", "D", "E", "FB2", "FC"},
    "pickup": {"B1", "B", "B2", "C", "D", "E", "FB2", "FC"},
    "van": {"B1", "B", "B2", "C", "D", "E", "FB2", "FC"},
    "truck": {"C", "FC"},
    "bus": {"D", "E", "FD", "FE"},
}


class RulesEngine:
    def verify(
        self,
        parsed_doc: ParsedDocument,
        image_result: Optional[ImageAnalysis] = None,
        driver_license_result: Optional[dict] = None,
    ) -> VerificationResult:
        reasons: List[str] = []
        flags: List[str] = []
        score = 0.0

        # ===== 1. document evidence =====
        incident_type = getattr(parsed_doc.claim, "incident_type", None)
        vehicle_type = getattr(parsed_doc.policy, "vehicle_type", None)
        claimed_damage = getattr(parsed_doc.claim, "claimed_damage", []) or []

        if incident_type == "vehicle_accident":
            reasons.append("Văn bản mô tả sự kiện tai nạn xe.")
            score += 0.15
        else:
            flags.append("incident_type_not_vehicle_accident")
            score -= 0.20

        if vehicle_type:
            reasons.append(f"Văn bản cho biết loại xe: {vehicle_type}.")
            score += 0.05
        else:
            flags.append("vehicle_type_missing_in_doc")
            score -= 0.05

        if claimed_damage:
            reasons.append(
                "Văn bản có hạng mục tổn thất: " + ", ".join(claimed_damage)
            )
            score += 0.05
        else:
            flags.append("claimed_damage_missing_in_doc")
            score -= 0.10

        # ===== 2. driver license check =====
        if driver_license_result is not None:
            dl_score, dl_reasons, dl_flags = self._check_driver_license(
                parsed_doc=parsed_doc,
                driver_license_result=driver_license_result,
            )
            score += dl_score
            reasons.extend(dl_reasons)
            flags.extend(dl_flags)

        # ===== 3. image section =====
        if image_result is None:
            return self._finalize(score, reasons, flags)

        # image_result là object/Pydantic -> dùng getattr
        ran_model = getattr(image_result, "ran_model", False)
        if not ran_model:
            flags.append("image_model_not_run")
            notes = getattr(image_result, "notes", []) or []
            flags.extend(notes)
            score -= 0.30
            return self._finalize(score, reasons, flags)

        model_name = getattr(image_result, "model_name", "unknown_model")
        reasons.append(f"Đã phân tích ảnh bằng {model_name}.")
        score += 0.05

        # ===== 4. vehicle presence =====
        vehicle_present = getattr(image_result, "vehicle_present", False)
        if vehicle_present:
            reasons.append("Ảnh có phương tiện.")
            score += 0.10
        else:
            flags.append("no_vehicle_detected")
            score -= 0.40

        # ===== 5. vehicle type matching =====
        doc_vehicle = self._normalize_vehicle_type(vehicle_type)
        img_vehicle = self._normalize_vehicle_type(getattr(image_result, "vehicle_type", None))

        if doc_vehicle and img_vehicle:
            if doc_vehicle == img_vehicle:
                reasons.append(f"Loại xe khớp giữa văn bản và ảnh: {img_vehicle}.")
                score += 0.10
            else:
                flags.append(f"vehicle_type_mismatch:{doc_vehicle}!={img_vehicle}")
                score -= 1

        # ===== 6. damage visibility =====
        is_damage_visible = getattr(image_result, "is_damage_visible", False)
        observed_damage = getattr(image_result, "damaged_parts", []) or []

        if is_damage_visible:
            reasons.append("Ảnh có hư hỏng nhìn thấy được.")
            score += 0.10
        else:
            flags.append("no_visible_damage")
            if doc_vehicle == "car":
                reasons.append("Xe ô tô có mặt trong ảnh nhưng không thấy hư hỏng rõ ràng.")
            elif doc_vehicle == "motorbike":
                reasons.append("Xe máy có mặt trong ảnh nhưng không thấy hư hỏng rõ ràng.")
            else:
                reasons.append("Phương tiện có mặt trong ảnh nhưng không thấy hư hỏng rõ ràng.")

            if claimed_damage:
                score -= 0.35
            else:
                score -= 0.10

        # ===== 7. damage matching =====
        damage_match_count, damage_total, damage_flags, damage_reasons = self._match_damage(
            claimed_damage,
            observed_damage,
        )
        flags.extend(damage_flags)
        reasons.extend(damage_reasons)

        if damage_total > 0:
            ratio = damage_match_count / damage_total
            score += 0.25 * ratio
            score -= 0.30 * (1 - ratio)

        # ===== 8. confidence =====
        confidence = getattr(image_result, "confidence", None)
        if confidence is not None:
            try:
                score += min(0.03, float(confidence) * 0.03)
            except Exception:
                pass

        notes = getattr(image_result, "notes", []) or []
        reasons.extend(notes)

        return self._finalize(score, reasons, flags)
    

    def _is_license_expired(self, expiry_date_str):
        if not expiry_date_str:
            return None

        text = str(expiry_date_str).strip()

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                exp = datetime.strptime(text, fmt).date()
                return exp < date.today()
            except ValueError:
                continue

        return None

    def _check_driver_license(
        self,
        parsed_doc,
        driver_license_result: dict,
    ) -> Tuple[float, List[str], List[str]]:
        reasons: List[str] = []
        flags: List[str] = []
        score = 0.0

        if not isinstance(driver_license_result, dict):
            flags.append("driver_license_invalid_format")
            return -0.10, reasons, flags

        # ===== đọc đúng theo output hiện tại của extract_driver.py =====
        is_driver_license = driver_license_result.get("is_driver_license", False)
        document_type = driver_license_result.get("document_type", "unknown")
        full_name = driver_license_result.get("full_name")
        license_class = driver_license_result.get("license_class")
        expiry_date = driver_license_result.get("expiry_date")
        short_reason = driver_license_result.get("short_reason", "")
        confidence = driver_license_result.get("confidence", 0.0)

        # fallback cho case analyzer fail
        ran_model = driver_license_result.get("ran_model", True)
        notes = driver_license_result.get("notes", []) or []

        if ran_model is False:
            flags.append("driver_license_model_not_run")
            flags.extend(notes)
            return -0.15, reasons, flags

        if not is_driver_license or document_type != "driver_license":
            flags.append("not_a_driver_license")
            if short_reason:
                reasons.append(short_reason)
            return -0.20, reasons, flags

        reasons.append("Đã kiểm tra bằng lái xe.")
        score += 0.05

        if short_reason:
            reasons.append(short_reason)

        # ===== check tên =====
        doc_name = self._extract_document_driver_name(parsed_doc)
        license_name = self._normalize_name(full_name)

        if doc_name and license_name:
            if doc_name == license_name:
                reasons.append("Tên trên bằng lái khớp với tên trên hồ sơ.")
                score += 0.12
            else:
                flags.append(f"driver_name_mismatch:{doc_name}!={license_name}")
                score -= 0.5
        else:
            flags.append("driver_name_missing_for_comparison")
            score -= 0.05

        # ===== check hạng bằng lái =====
        doc_vehicle = self._normalize_vehicle_type(getattr(parsed_doc.policy, "vehicle_type", None))
        normalized_license_class = self._normalize_license_class(license_class)

        if doc_vehicle and normalized_license_class:
            allowed_classes = VEHICLE_LICENSE_COMPATIBILITY.get(doc_vehicle, set())

            if not allowed_classes:
                flags.append(f"unknown_vehicle_type_for_license_check:{doc_vehicle}")
                score -= 0.03
            elif normalized_license_class in allowed_classes:
                reasons.append(
                    f"Hạng bằng lái {normalized_license_class} phù hợp với phương tiện {doc_vehicle}."
                )
                score += 0.12
            else:
                flags.append(
                    f"driver_license_not_compatible:{normalized_license_class}!={doc_vehicle}"
                )
                score -= 0.30
        else:
            flags.append("insufficient_data_for_license_vehicle_check")
            score -= 0.05

        # ===== check hết hạn từ expiry_date =====
        expired = self._is_license_expired(expiry_date)
        if expired is True:
            flags.append("driver_license_expired")
            score -= 0.25
        elif expired is False:
            reasons.append("Bằng lái còn hiệu lực.")
            score += 0.05
        else:
            flags.append("driver_license_expiry_unknown")

        # ===== confidence =====
        try:
            score += min(0.03, float(confidence) * 0.03)
        except Exception:
            pass

        return score, reasons, flags

    def _extract_document_driver_name(self, parsed_doc) -> Optional[str]:
        candidates = [
            getattr(parsed_doc.claim, "driver_name", None),
            getattr(parsed_doc.claim, "claimant_name", None),

            # thêm dòng này
            getattr(parsed_doc.policy, "claimant_name", None),

            getattr(parsed_doc.policy, "insured_name", None),
            getattr(parsed_doc.policy, "policyholder_name", None),
            getattr(parsed_doc.policy, "owner_name", None),
        ]

        for value in candidates:
            norm = self._normalize_name(value)
            if norm:
                return norm
        return None

    def _match_damage(
        self,
        claimed_damage: List[str],
        observed_damage: List[str],
    ) -> Tuple[int, int, List[str], List[str]]:
        flags: List[str] = []
        reasons: List[str] = []

        if not claimed_damage:
            return 0, 0, flags, reasons

        observed_set = {self._normalize_damage(x) for x in observed_damage if x}
        matched = 0

        for damage in claimed_damage:
            norm_damage = self._normalize_damage(damage)
            allowed_matches = DAMAGE_EQUIVALENTS.get(norm_damage, {norm_damage})

            if observed_set.intersection(allowed_matches):
                matched += 1
                reasons.append(f"Hạng mục tổn thất khớp ảnh: {norm_damage}.")
            else:
                flags.append(f"damage_not_matched:{norm_damage}")

        extra_damage = []
        claimed_set = {self._normalize_damage(x) for x in claimed_damage if x}
        for d in observed_set:
            if d not in claimed_set:
                extra_damage.append(d)

        if extra_damage:
            reasons.append("Ảnh còn cho thấy thêm: " + ", ".join(sorted(extra_damage)))

        return matched, len(claimed_damage), flags, reasons

    def _normalize_name(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return None
        return " ".join(str(name).strip().lower().split())

    def _normalize_vehicle_type(self, vehicle_type: Optional[str]) -> Optional[str]:
        if not vehicle_type:
            return None

        v = str(vehicle_type).strip().lower()

        aliases = {
            "xe máy": "motorbike",
            "xe may": "motorbike",
            "motorbike": "motorbike",
            "motorcycle": "motorbike",
            "moto": "motorbike",
            "ô tô": "car",
            "ôtô": "car",
            "oto": "car",
            "o to": "car",
            "car": "car",
            "sedan": "car",
            "suv": "car",
            "pickup": "pickup",
            "van": "van",
            "truck": "truck",
            "xe tải": "truck",
            "xe tai": "truck",
            "bus": "bus",
            "xe khách": "bus",
            "xe khach": "bus",
        }
        return aliases.get(v, v)

    def _normalize_license_class(self, license_class: Optional[str]) -> Optional[str]:
        if not license_class:
            return None
        return str(license_class).strip().upper().replace(".", "")

    def _normalize_damage(self, damage: Optional[str]) -> Optional[str]:
        if not damage:
            return None
        return str(damage).strip().lower()

    def _finalize(
        self,
        score: float,
        reasons: List[str],
        flags: List[str],
    ) -> VerificationResult:
        flags = list(dict.fromkeys(flags))
        reasons = list(dict.fromkeys(reasons))

        score = max(0.0, min(1.0, score))

        # hard fail
        if "driver_license_expired" in flags:
            decision = "inconsistent"
        elif "no_vehicle_detected" in flags:
            decision = "inconsistent"
        elif any(f.startswith("driver_license_not_compatible:") for f in flags):
            decision = "inconsistent"

        # tên lệch -> review tay
        elif any(f.startswith("driver_name_mismatch:") for f in flags):
            decision = "manual_review"

        # ảnh không thấy damage -> review tay, đừng reject cứng
        elif "no_visible_damage" in flags:
            decision = "manual_review"

        elif not flags and score >= 0.55:
            decision = "consistent"
        elif score >= 0.40:
            decision = "manual_review"
        else:
            decision = "inconsistent"

        return VerificationResult(
            decision=decision,
            reasons=reasons,
            flags=flags,
            score=round(score, 4),
        )