from pydantic import BaseModel

from app.models.settings import PreferredContact, SettingsPublic


class SettingsUpdateRequest(BaseModel):
    push_notif: bool | None = None
    email_notif: bool | None = None
    in_app_notif: bool | None = None
    claim_updates: bool | None = None
    doc_reminders: bool | None = None
    marketing_emails: bool | None = None
    preferred_contact: PreferredContact | None = None
    language: str | None = None


class SettingsResponse(SettingsPublic):
    pass

