from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Literal


class ConsentPurposeResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str
    is_required: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsentNoticeResponse(BaseModel):
    id: int
    purpose_id: int
    version: str
    title: str
    content: str
    is_active: bool
    published_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsentDecisionRequest(BaseModel):
    notice_id: int
    status: Literal["granted", "denied"]
    collection_method: Literal["web", "android"]


class ConsentWithdrawalRequest(BaseModel):
    purpose_id: int
    collection_method: Literal["web", "android"]


class MyConsentResponse(BaseModel):
    id: int
    purpose_id: int
    notice_id: int
    notice_version: str
    status: str
    collection_method: str
    consented_at: datetime | None
    withdrawn_at: datetime | None
    created_at: datetime

class ConsentAuditResponse(BaseModel):
    id: int
    consent_record_id: int | None
    action: str
    previous_status: str | None
    new_status: str | None
    collection_method: str
    created_at: datetime