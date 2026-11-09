"""Test case model (CF-01, DS-05).

A row is either a confirmed *reference* animation or a *test case* that links to one.
Test cases are grouped by their reference; there is no separate dataset entity yet.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import field_validator, model_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.error_types import ERROR_TYPES, NO_ERROR, ErrorCategory

# IDs are also used as file names for uploads, so they must be filesystem safe.
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,31}$")


class TestCaseKind(str, Enum):
    REFERENCE = "reference"
    TESTCASE = "testcase"


class ExpectedResult(str, Enum):
    OK = "OK"
    NOK = "NOK"


class TestCaseSource(str, Enum):
    SEED = "seed"  # imported from dataset/testcases.csv, read-only via the API
    UPLOAD = "upload"  # uploaded by a user (DS-07)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestCaseBase(SQLModel):
    id: str = Field(primary_key=True)
    kind: TestCaseKind
    name: str
    description: str = ""
    reference_id: str | None = Field(default=None, foreign_key="testcase.id", index=True)
    expected_result: ExpectedResult
    error_type: str
    category: ErrorCategory
    is_edge_case: bool = False
    source: TestCaseSource
    sha256: str
    created_at: datetime = Field(default_factory=_utcnow)


class TestCase(TestCaseBase, table=True):
    __tablename__ = "testcase"
    __test__ = False  # keep pytest from collecting this class

    # Video path relative to the dataset dir (seed) or the upload dir (upload).
    file: str
    # How the case was produced from the reference (DS-06), e.g. {"params": {"popupDelay": 500}}.
    manipulation: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))


class TestCaseRead(TestCaseBase):
    __test__ = False

    manipulation: dict[str, Any] | None = None
    video_url: str

    @classmethod
    def from_db(cls, tc: TestCase) -> TestCaseRead:
        return cls.model_validate(tc, update={"video_url": f"/api/testcases/{tc.id}/video"})


class TestCaseCreate(SQLModel):
    """Metadata sent together with an uploaded clip (DS-07)."""

    __test__ = False

    id: str | None = None
    kind: TestCaseKind = TestCaseKind.TESTCASE
    name: str
    description: str = ""
    reference_id: str | None = None
    expected_result: ExpectedResult
    error_type: str = NO_ERROR
    is_edge_case: bool = False

    @field_validator("id", "reference_id", mode="before")
    @classmethod
    def _empty_to_none(cls, v: Any) -> Any:
        return None if isinstance(v, str) and not v.strip() else v

    @field_validator("id")
    @classmethod
    def _check_id(cls, v: str | None) -> str | None:
        if v is not None and not ID_PATTERN.match(v):
            raise ValueError("ID may only contain letters, digits, '-' and '_' (max. 32 characters)")
        return v

    @field_validator("name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name must not be empty")
        return v.strip()

    @field_validator("error_type")
    @classmethod
    def _check_error_type(cls, v: str) -> str:
        if v not in ERROR_TYPES:
            raise ValueError(f"Unknown error type '{v}'. Allowed: {', '.join(ERROR_TYPES)}")
        return v

    @model_validator(mode="after")
    def _check_consistency(self) -> TestCaseCreate:
        if self.kind == TestCaseKind.REFERENCE:
            if self.reference_id is not None:
                raise ValueError("A reference must not link to another reference")
            if self.expected_result != ExpectedResult.OK or self.error_type != NO_ERROR:
                raise ValueError("A reference must be expected OK with error type 'none'")
        else:
            if self.reference_id is None:
                raise ValueError("A test case must link to a reference")
            if self.expected_result == ExpectedResult.NOK and self.error_type == NO_ERROR:
                raise ValueError("A NOK test case needs an error type other than 'none'")
        return self
