import re
import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EnvironmentEnum(str, Enum):
    DEV = "Dev"
    QA = "QA"
    UAT = "UAT"
    PROD = "Prod"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            val_upper = value.strip().upper()
            mapping = {
                "DEV": cls.DEV,
                "DEVELOPMENT": cls.DEV,
                "QA": cls.QA,
                "UAT": cls.UAT,
                "PROD": cls.PROD,
                "PRODUCTION": cls.PROD,
            }
            if val_upper in mapping:
                return mapping[val_upper]
        return None


class CaseStatusEnum(str, Enum):
    NOT_RUN = "not_run"
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class SessionStatusEnum(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# ---------------------------------------------------------------------------
# Attachment Schemas
# ---------------------------------------------------------------------------
class AttachmentBase(BaseModel):
    caption: Optional[str] = Field(None, max_length=255)


class AttachmentUpdateCaption(BaseModel):
    caption: Optional[str] = Field(None, max_length=255)


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_case_id: uuid.UUID
    file_path: str
    caption: Optional[str] = None
    figure_no: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Test Step Schemas
# ---------------------------------------------------------------------------
class TestStepCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=1000)


class TestStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_case_id: uuid.UUID
    step_no: int
    description: str


# ---------------------------------------------------------------------------
# Test Case Schemas
# ---------------------------------------------------------------------------
class TestCaseCreate(BaseModel):
    scenario: Optional[str] = Field(None, max_length=500)
    precondition: Optional[str] = Field(None, max_length=5000)
    test_data: Optional[str] = Field(None, max_length=5000)
    expected_result: Optional[str] = Field(None, max_length=5000)
    actual_result: Optional[str] = Field(None, max_length=5000)
    status: Optional[CaseStatusEnum] = CaseStatusEnum.NOT_RUN
    steps: Optional[List[TestStepCreate]] = Field(None, max_length=50)


class TestCaseUpdate(BaseModel):
    scenario: Optional[str] = Field(None, max_length=500)
    precondition: Optional[str] = Field(None, max_length=5000)
    test_data: Optional[str] = Field(None, max_length=5000)
    expected_result: Optional[str] = Field(None, max_length=5000)
    actual_result: Optional[str] = Field(None, max_length=5000)
    status: Optional[CaseStatusEnum] = None
    steps: Optional[List[TestStepCreate]] = Field(None, max_length=50)


class TestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    session_id: uuid.UUID
    tc_id: str
    position: int
    scenario: Optional[str] = None
    precondition: Optional[str] = None
    test_data: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    status: str
    executed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    steps: List[TestStepResponse] = Field(default_factory=list, validation_alias="test_steps")
    attachments: List[AttachmentResponse] = Field(default_factory=list)


class CaseReorderRequest(BaseModel):
    ordered_case_ids: List[uuid.UUID]


# ---------------------------------------------------------------------------
# Session Schemas
# ---------------------------------------------------------------------------
def validate_tc_prefix(v: Optional[str]) -> str:
    if v is None:
        return "TC"
    if not isinstance(v, str):
        raise ValueError("tc_prefix must be a string")
    v = v.strip().upper()
    if not v:
        return "TC"
    if len(v) > 12:
        raise ValueError("tc_prefix cannot exceed 12 characters")
    if not re.match(r"^[A-Z0-9-]+$", v):
        raise ValueError("tc_prefix may only contain letters, digits, and hyphens")
    return v


class SessionCreate(BaseModel):
    ticket_no: str = Field(..., min_length=1, max_length=100)
    ticket_title: str = Field(..., min_length=1, max_length=255)
    environment: Optional[EnvironmentEnum] = None
    test_date: Optional[date] = None
    testing_types: List[str] = Field(default_factory=list)
    tc_prefix: Optional[str] = Field("TC", max_length=12)

    @field_validator("tc_prefix", mode="before")
    @classmethod
    def check_tc_prefix(cls, v: Any) -> str:
        return validate_tc_prefix(v)


class SessionUpdate(BaseModel):
    ticket_no: Optional[str] = Field(None, min_length=1, max_length=100)
    ticket_title: Optional[str] = Field(None, min_length=1, max_length=255)
    environment: Optional[EnvironmentEnum] = None
    test_date: Optional[date] = None
    testing_types: Optional[List[str]] = None
    tc_prefix: Optional[str] = None

    @field_validator("tc_prefix", mode="before")
    @classmethod
    def check_tc_prefix(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return validate_tc_prefix(v)


class SessionCounts(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pass_count: int = Field(0, alias="pass", serialization_alias="pass")
    fail: int = 0
    blocked: int = 0
    skipped: int = 0
    not_run: int = 0
    total: int = 0


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    ticket_no: str
    ticket_title: str
    environment: Optional[str] = None
    test_date: Optional[date] = None
    testing_types: List[str] = []
    tc_prefix: str
    tc_counter: int
    status: str
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SessionDetailResponse(SessionResponse):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    cases: List[TestCaseResponse] = Field(default_factory=list, validation_alias="test_cases")
    counts: SessionCounts
