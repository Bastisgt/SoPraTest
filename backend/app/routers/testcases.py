"""Test case & dataset management API (CF-01)."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlmodel import Session, select

from app.core.config import Settings
from app.core.deps import get_session, get_settings
from app.models.error_types import ERROR_TYPES, ErrorType, category_of
from app.models.testcase import (
    ExpectedResult,
    TestCase,
    TestCaseCreate,
    TestCaseKind,
    TestCaseRead,
    TestCaseSource,
)
from app.services.storage import ALLOWED_VIDEO_EXTENSIONS, UploadTooLargeError, save_upload, video_path

router = APIRouter(prefix="/api", tags=["testcases"])

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _get_or_404(session: Session, testcase_id: str) -> TestCase:
    tc = session.get(TestCase, testcase_id)
    if tc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Test case '{testcase_id}' not found")
    return tc


def _next_upload_id(session: Session) -> str:
    n = 1
    while session.get(TestCase, f"UP-{n:03d}") is not None:
        n += 1
    return f"UP-{n:03d}"


@router.get("/error-types", response_model=list[ErrorType])
def list_error_types() -> list[ErrorType]:
    return list(ERROR_TYPES.values())


@router.get("/testcases", response_model=list[TestCaseRead])
def list_testcases(
    session: SessionDep,
    kind: TestCaseKind | None = None,
    reference_id: str | None = None,
    expected_result: ExpectedResult | None = None,
) -> list[TestCaseRead]:
    query = select(TestCase).order_by(TestCase.kind, TestCase.id)
    if kind is not None:
        query = query.where(TestCase.kind == kind)
    if reference_id is not None:
        query = query.where(TestCase.reference_id == reference_id)
    if expected_result is not None:
        query = query.where(TestCase.expected_result == expected_result)
    return [TestCaseRead.from_db(tc) for tc in session.exec(query)]


@router.get("/testcases/{testcase_id}", response_model=TestCaseRead)
def get_testcase(testcase_id: str, session: SessionDep) -> TestCaseRead:
    return TestCaseRead.from_db(_get_or_404(session, testcase_id))


@router.get("/testcases/{testcase_id}/video", response_class=FileResponse)
def get_testcase_video(testcase_id: str, session: SessionDep, settings: SettingsDep) -> FileResponse:
    path = video_path(_get_or_404(session, testcase_id), settings)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Video file for '{testcase_id}' is missing")
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type)


@router.post("/testcases", response_model=TestCaseRead, status_code=status.HTTP_201_CREATED)
async def upload_testcase(
    session: SessionDep,
    settings: SettingsDep,
    file: Annotated[UploadFile, File(description="Video clip")],
    name: Annotated[str, Form()],
    expected_result: Annotated[ExpectedResult, Form()],
    kind: Annotated[TestCaseKind, Form()] = TestCaseKind.TESTCASE,
    error_type: Annotated[str, Form()] = "none",
    reference_id: Annotated[str | None, Form()] = None,
    is_edge_case: Annotated[bool, Form()] = False,
    description: Annotated[str, Form()] = "",
    id: Annotated[str | None, Form(description="Optional; generated (UP-###) if empty")] = None,
) -> TestCaseRead:
    """Uploads a clip as a new reference or test case (DS-07)."""
    try:
        data = TestCaseCreate(
            id=id,
            kind=kind,
            name=name,
            description=description,
            reference_id=reference_id,
            expected_result=expected_result,
            error_type=error_type,
            is_edge_case=is_edge_case,
        )
    except ValidationError as exc:
        raise HTTPException(
            422,
            [err["msg"] for err in exc.errors(include_url=False)],
        ) from exc

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            422,
            f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}",
        )

    testcase_id = data.id or _next_upload_id(session)
    if session.get(TestCase, testcase_id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Test case '{testcase_id}' already exists")

    if data.reference_id is not None:
        ref = session.get(TestCase, data.reference_id)
        if ref is None or ref.kind != TestCaseKind.REFERENCE:
            raise HTTPException(
                422, f"'{data.reference_id}' is not an existing reference"
            )

    file_name = f"{testcase_id}{ext}"
    try:
        sha256 = await save_upload(file, settings.upload_dir / file_name, settings.max_upload_bytes)
    except UploadTooLargeError as exc:
        raise HTTPException(
            413, f"File exceeds {settings.max_upload_mb} MB"
        ) from exc

    tc = TestCase(
        **data.model_dump(exclude={"id"}),
        id=testcase_id,
        category=category_of(data.error_type),
        source=TestCaseSource.UPLOAD,
        sha256=sha256,
        file=file_name,
    )
    session.add(tc)
    session.commit()
    session.refresh(tc)
    return TestCaseRead.from_db(tc)


@router.delete("/testcases/{testcase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_testcase(testcase_id: str, session: SessionDep, settings: SettingsDep) -> None:
    """Deletes an uploaded test case. Seed test cases are managed by dataset/generate.py."""
    tc = _get_or_404(session, testcase_id)
    if tc.source == TestCaseSource.SEED:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Dataset test cases are read-only; change them via dataset/generate.py"
        )
    dependents = session.exec(select(TestCase.id).where(TestCase.reference_id == tc.id)).all()
    if dependents:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Reference is still used by: {', '.join(dependents)}"
        )
    path = video_path(tc, settings)
    session.delete(tc)
    session.commit()
    path.unlink(missing_ok=True)
