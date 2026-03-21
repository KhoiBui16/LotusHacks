import json
from typing import Any, Dict, Optional

from .file_reader import read_text_file
from .text_extractor import ClaimExtractor
from .image_analyzer import ImageAnalyzer
from .extract_driver import DriverLicenseAnalyzer, DriverLicenseOutput
from .rules_engine import RulesEngine


def run_claim_verification(
    doc_path: str,
    image_path: str,
    driver_license_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Chạy toàn bộ pipeline xác thực claim bảo hiểm.

    Args:
        doc_path: đường dẫn file claim (docx/pdf/txt...)
        image_path: đường dẫn ảnh tai nạn / ảnh xe
        driver_license_path: đường dẫn ảnh GPLX, có thể None

    Returns:
        Dict kết quả đầy đủ gồm:
        - policy
        - claim
        - image_result
        - driver_license_result
        - verification
    """

    # 1. Đọc văn bản
    doc_result = read_text_file(doc_path)

    # 2. Parse claim từ text
    extractor = ClaimExtractor()
    parsed_doc = extractor.extract(
        file_name=doc_result["file_name"],
        file_type=doc_result["file_type"],
        cleaned_text=doc_result["cleaned_text"],
        num_chars=doc_result["num_chars"],
    )

    # 3. Phân tích ảnh tai nạn
    image_analyzer = ImageAnalyzer()
    image_result = image_analyzer.analyze(image_path)

    # 4. Phân tích GPLX
    driver_license_result = None
    if driver_license_path:
        driver_license_analyzer = DriverLicenseAnalyzer()
        dl_result = driver_license_analyzer.analyze(driver_license_path)

        if isinstance(dl_result, DriverLicenseOutput):
            driver_license_result = dl_result.model_dump()
        else:
            driver_license_result = dl_result

    # 5. Verify claim
    rules = RulesEngine()
    verification = rules.verify(parsed_doc, image_result, driver_license_result)

    # 6. Trả kết quả
    output = {
        "policy": parsed_doc.policy.model_dump(),
        "claim": parsed_doc.claim.model_dump(),
        "image_result": image_result.model_dump(),
        "driver_license_result": driver_license_result,
        "verification": verification.model_dump(),
    }

    return output


def run_and_print(
    doc_path: str,
    image_path: str,
    driver_license_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Hàm tiện ích để chạy pipeline và print JSON đẹp ra màn hình.
    """
    output = run_claim_verification(
        doc_path=doc_path,
        image_path=image_path,
        driver_license_path=driver_license_path,
    )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return output