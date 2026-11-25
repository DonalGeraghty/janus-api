"""Structured Budget request and provider response schemas."""
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ForecastModel(StrictModel):
    @field_validator('amount_eur', 'save_more', 'balanced', 'breathing_room', mode='before', check_fields=False)
    @classmethod
    def numeric_money(cls, value):
        # Some provider parsers supply JSON numbers. Accept exact cents without
        # relaxing finite/nonnegative/magnitude constraints or guessing locale.
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            try:
                amount = Decimal(str(value))
                if amount.is_finite() and amount == amount.quantize(Decimal('0.01')):
                    return format(amount, 'f')
            except InvalidOperation:
                pass
        return value


class Assumption(ForecastModel):
    id: str = Field(min_length=1, max_length=64)
    kind: Literal["income", "bill"]
    label: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=120)
    amount_eur: str = Field(pattern=r"^\d{1,8}(\.\d{1,2})?$")
    due_date: date
    status: Literal["expected", "paid", "not_recurring"] = "expected"
    confidence: Literal["high", "medium", "low"]
    evidence: str = Field(min_length=1, max_length=300)
    basis: Literal["history", "seasonal"]


class Limits(ForecastModel):
    save_more: str = Field(pattern=r"^\d{1,8}(\.\d{1,2})?$")
    balanced: str = Field(pattern=r"^\d{1,8}(\.\d{1,2})?$")
    breathing_room: str = Field(pattern=r"^\d{1,8}(\.\d{1,2})?$")


class Category(ForecastModel):
    category: str = Field(min_length=1, max_length=120)
    fixed: bool
    remaining: Limits
    confidence: Literal["high", "medium", "low"]
    reason: str = Field(min_length=1, max_length=300)


class ModeAnalysis(StrictModel):
    save_more: str = Field(min_length=1, max_length=400)
    balanced: str = Field(min_length=1, max_length=400)
    breathing_room: str = Field(min_length=1, max_length=400)

    @field_validator('save_more', 'balanced', 'breathing_room')
    @classmethod
    def single_paragraph(cls, value):
        return ' '.join(value.split())


class Proposal(StrictModel):
    analysis: ModeAnalysis
    assumptions: list[Assumption] = Field(max_length=40)
    categories: list[Category] = Field(max_length=40)


class PlanRequest(StrictModel):
    """Assessment has no user-editable planning inputs."""
    pass
