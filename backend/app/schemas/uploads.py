from pydantic import BaseModel, Field

from app.models.upload import UploadPurpose


class UploadResponse(BaseModel):
    upload_id: str = Field(alias="id")
    filename: str
    content_type: str
    size_bytes: int
    purpose: UploadPurpose
    url: str

