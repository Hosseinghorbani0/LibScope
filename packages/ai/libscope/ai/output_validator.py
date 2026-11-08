"""
AI Output Validator.
Defensively validates and sanitizes outputs returned from askai-python before returning to business logic.
"""
from typing import Any

from libscope.ai.exceptions import LibScopeAIValidationError
from libscope.core.logging import get_logger
from pydantic import BaseModel, ValidationError

logger = get_logger("ai.validator")


class AIOutputValidator:
    """Validates structured AI responses against expected Pydantic models."""

    @staticmethod
    def validate_model(output: Any, expected_model: type[BaseModel]) -> BaseModel:
        """
        Validate that output matches expected Pydantic model.
        Accepts model instance, dict, or json string.
        """
        if isinstance(output, expected_model):
            return output

        if isinstance(output, dict):
            try:
                return expected_model.model_validate(output)
            except ValidationError as err:
                raise LibScopeAIValidationError(f"Pydantic model validation failed: {err}") from err

        if isinstance(output, str):
            clean = output.strip()
            # If wrapped in code blocks, extract
            if clean.startswith("```json") and clean.endswith("```"):
                clean = clean[7:-3].strip()
            elif clean.startswith("```") and clean.endswith("```"):
                clean = clean[3:-3].strip()

            try:
                return expected_model.model_validate_json(clean)
            except Exception as err:
                raise LibScopeAIValidationError(f"Failed to parse and validate JSON text to {expected_model.__name__}: {err}") from err

        raise LibScopeAIValidationError(f"Unsupported output type for validation: {type(output)}")

    @staticmethod
    def sanitize_text(text: str | None, default: str = "No data returned") -> str:
        """Sanitize raw text response, ensuring non-empty output."""
        if not text or not str(text).strip():
            return default
        return str(text).strip()

