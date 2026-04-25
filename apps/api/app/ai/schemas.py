from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class StructuredAIResponse(BaseModel):
    raw_text: str
    data: dict[str, Any]
    provider: str
    model: str


class AIValidationFailure(Exception):
    def __init__(self, message: str, raw_text: str) -> None:
        super().__init__(message)
        self.raw_text = raw_text


def validate_structured_output(model: type[T], payload: dict[str, Any], raw_text: str = "") -> T:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise AIValidationFailure(str(exc), raw_text) from exc

