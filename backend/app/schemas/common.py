from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None


class ApiErrorResponse(BaseModel):
    success: bool = False
    data: None = None
    message: str
    code: str
