"""Catalogue of animation error types (DS-03, DS-04).

Mirrors CATEGORY in dataset/generate.py. To add an error type, add it here (and in the
generator if test cases for it should be generated).
"""

from enum import Enum

from pydantic import BaseModel


class ErrorCategory(str, Enum):
    NONE = "none"
    TIMING = "timing"  # movement / timing errors
    DISPLAY = "display"  # display errors


class ErrorType(BaseModel):
    id: str
    category: ErrorCategory
    description: str


NO_ERROR = "none"

ERROR_TYPES: dict[str, ErrorType] = {
    e.id: e
    for e in [
        ErrorType(id=NO_ERROR, category=ErrorCategory.NONE, description="No error"),
        ErrorType(id="popup_delay", category=ErrorCategory.TIMING, description="Pop-up appears too late"),
        ErrorType(id="highlight_timing", category=ErrorCategory.TIMING, description="Focus highlight moves with wrong timing"),
        ErrorType(id="animation_speed", category=ErrorCategory.TIMING, description="Animation is too fast or too slow"),
        ErrorType(id="frame_freeze", category=ErrorCategory.TIMING, description="Display freezes for a period of time"),
        ErrorType(id="missing_element", category=ErrorCategory.DISPLAY, description="A UI element is missing"),
        ErrorType(id="wrong_content", category=ErrorCategory.DISPLAY, description="Wrong text, icon or colour"),
        ErrorType(id="flicker", category=ErrorCategory.DISPLAY, description="Display flickers"),
    ]
}


def category_of(error_type: str) -> ErrorCategory:
    return ERROR_TYPES[error_type].category
