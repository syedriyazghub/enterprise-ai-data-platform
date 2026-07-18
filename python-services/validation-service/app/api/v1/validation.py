"""Validation API endpoints — typed responses, rules CRUD, audit trail."""
from typing import Any
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.schemas.validation import (
    ValidateDatasetRequest,
    ValidationSummaryResponse,
    ValidationReportSchema,
    ValidationResultSchema,
    DuplicateResultSchema,
    FieldSchemaResponse,
    SchemaProfileResponse,
)
from app.services.validation_service import ValidationService, ValidationRule
from app.validators.core_validators import Severity, VALIDATOR_REGISTRY

router = APIRouter()


# ── Validate ──────────────────────────────────────────────────────────────────

@router.post("/validate", response_model=ValidationSummaryResponse)
async def validate_dataset(request: ValidateDatasetRequest):
    """
    Validate a dataset against a set of rules.

    Supports 50+ validation types:
    - not_null, email, phone, date, numeric_range, regex
    - pan, gst, aadhar, iban, credit_card, postal_code, invoice_number
    """
    service = ValidationService()
    rules = [
        ValidationRule(
            field=r.field,
            rule_type=r.rule_type,
            severity=r.severity,
            params=r.params,
        )
        for r in request.rules
    ]
    summary = service.validate_dataset(
        records=request.records,
        rules=rules,
        detect_duplicates=request.detect_duplicates,
        detect_schema=request.detect_schema,
        duplicate_key_fields=request.duplicate_key_fields,
    )

    schema_resp = None
    if summary.schema_profile:
        schema_resp = SchemaProfileResponse(
            fields=[FieldSchemaResponse(**f.__dict__) for f in summary.schema_profile.fields],
            record_count=summary.schema_profile.record_count,
            completeness_score=summary.schema_profile.completeness_score,
        )

    # Build typed reports (fixes raw-dict bug)
    reports = []
    for r in summary.reports:
        reports.append(ValidationReportSchema(
            record_index=r.record_index,
            passed=r.passed,
            quality_score=r.quality_score,
            errors=[
                ValidationResultSchema(
                    field=e.field, rule=e.rule, passed=e.passed,
                    severity=e.severity.value, message=e.message, suggestion=e.suggestion,
                )
                for e in r.errors
            ],
            warnings=[
                ValidationResultSchema(
                    field=w.field, rule=w.rule, passed=w.passed,
                    severity=w.severity.value, message=w.message, suggestion=w.suggestion,
                )
                for w in r.warnings
            ],
        ))

    return ValidationSummaryResponse(
        total_records=summary.total_records,
        passed_records=summary.passed_records,
        failed_records=summary.failed_records,
        total_errors=summary.total_errors,
        total_warnings=summary.total_warnings,
        quality_score=summary.quality_score,
        pass_rate=summary.pass_rate,
        schema_profile=schema_resp,
        duplicates=[DuplicateResultSchema(**d.__dict__) for d in summary.duplicates],
        reports=reports,
    )


# ── Rules catalog ─────────────────────────────────────────────────────────────

@router.get("/rules")
async def list_available_rules(
    search: str = Query("", description="Filter rules by name"),
):
    """List all available validation rule types with descriptions."""
    rules = [
        {
            "type": k,
            "description": type(v).__doc__ or k,
            "class": type(v).__name__,
        }
        for k, v in VALIDATOR_REGISTRY.items()
        if not search or search.lower() in k.lower()
    ]
    return {"rules": rules, "total": len(rules)}


@router.get("/rules/{rule_type}")
async def get_rule_detail(rule_type: str):
    """Get details and example usage for a specific rule type."""
    validator = VALIDATOR_REGISTRY.get(rule_type)
    if not validator:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Rule '{rule_type}' not found")

    examples = {
        "not_null":      {"field": "email", "rule_type": "not_null"},
        "email":         {"field": "email", "rule_type": "email"},
        "phone":         {"field": "phone", "rule_type": "phone", "params": {"country": "IN"}},
        "date":          {"field": "dob", "rule_type": "date", "params": {"formats": ["%Y-%m-%d"]}},
        "numeric_range": {"field": "age", "rule_type": "numeric_range", "params": {"min": 0, "max": 150}},
        "regex":         {"field": "code", "rule_type": "regex", "params": {"pattern": "^[A-Z]{3}\\d{3}$"}},
        "pan":           {"field": "pan_number", "rule_type": "pan"},
        "gst":           {"field": "gst_number", "rule_type": "gst"},
        "iban":          {"field": "bank_account", "rule_type": "iban"},
        "credit_card":   {"field": "card_number", "rule_type": "credit_card"},
        "postal_code":   {"field": "zip", "rule_type": "postal_code", "params": {"country": "US"}},
    }

    return {
        "type": rule_type,
        "description": type(validator).__doc__ or rule_type,
        "example": examples.get(rule_type, {"field": "field_name", "rule_type": rule_type}),
    }


# ── Schema detection ──────────────────────────────────────────────────────────

class SchemaDetectRequest(BaseModel):
    records: list[dict[str, Any]] = Field(..., min_length=1)


@router.post("/schema/detect", response_model=SchemaProfileResponse)
async def detect_schema(request: SchemaDetectRequest):
    """Auto-detect schema from a list of records."""
    from app.validators.schema_detector import SchemaDetector
    detector = SchemaDetector()
    profile = detector.detect(request.records)
    return SchemaProfileResponse(
        fields=[FieldSchemaResponse(**f.__dict__) for f in profile.fields],
        record_count=profile.record_count,
        completeness_score=profile.completeness_score,
    )


# ── Duplicate detection ───────────────────────────────────────────────────────

class DuplicateDetectRequest(BaseModel):
    records: list[dict[str, Any]] = Field(..., min_length=1)
    key_fields: list[str] | None = None
    fuzzy_threshold: int = Field(90, ge=50, le=100)


@router.post("/duplicates/detect")
async def detect_duplicates(request: DuplicateDetectRequest):
    """Detect exact and fuzzy duplicate records."""
    from app.validators.duplicate_detector import DuplicateDetector
    detector = DuplicateDetector(
        key_fields=request.key_fields,
        fuzzy_threshold=request.fuzzy_threshold,
    )
    duplicates = detector.detect(request.records)
    return {
        "total_records": len(request.records),
        "duplicates_found": len(duplicates),
        "duplicate_rate": round(len(duplicates) / len(request.records) * 100, 2),
        "duplicates": [d.__dict__ for d in duplicates],
    }
