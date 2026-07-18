"""Pydantic schemas for validation service."""
from typing import Any, Optional
from pydantic import BaseModel, Field
from app.validators.core_validators import Severity


class ValidationRuleSchema(BaseModel):
    field: str
    rule_type: str
    severity: Severity = Severity.ERROR
    params: dict[str, Any] = Field(default_factory=dict)


class ValidateDatasetRequest(BaseModel):
    records: list[dict[str, Any]] = Field(..., min_length=1)
    rules: list[ValidationRuleSchema]
    detect_duplicates: bool = True
    detect_schema: bool = True
    duplicate_key_fields: Optional[list[str]] = None


class ValidationResultSchema(BaseModel):
    field: str
    rule: str
    passed: bool
    severity: str
    message: str
    suggestion: str = ""


class ValidationReportSchema(BaseModel):
    record_index: int
    passed: bool
    quality_score: float
    errors: list[ValidationResultSchema]
    warnings: list[ValidationResultSchema]


class DuplicateResultSchema(BaseModel):
    record_index: int
    duplicate_of: int
    similarity_score: float
    match_type: str
    matched_fields: list[str]


class FieldSchemaResponse(BaseModel):
    name: str
    detected_type: str
    nullable: bool
    null_count: int
    unique_count: int


class SchemaProfileResponse(BaseModel):
    fields: list[FieldSchemaResponse]
    record_count: int
    completeness_score: float


class ValidationSummaryResponse(BaseModel):
    total_records: int
    passed_records: int
    failed_records: int
    total_errors: int
    total_warnings: int
    quality_score: float
    pass_rate: float
    schema_profile: Optional[SchemaProfileResponse] = None
    duplicates: list[DuplicateResultSchema]
    reports: list[ValidationReportSchema]
