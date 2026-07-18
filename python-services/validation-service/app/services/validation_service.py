"""Validation orchestration service."""
from dataclasses import dataclass, field
from typing import Any
import structlog

from app.validators.core_validators import get_validator, ValidationReport, ValidationResult, Severity
from app.validators.duplicate_detector import DuplicateDetector, DuplicateResult
from app.validators.schema_detector import SchemaDetector, SchemaProfile

logger = structlog.get_logger()


@dataclass
class ValidationRule:
    field: str
    rule_type: str
    severity: Severity = Severity.ERROR
    params: dict = field(default_factory=dict)


@dataclass
class ValidationSummary:
    total_records: int
    passed_records: int
    failed_records: int
    total_errors: int
    total_warnings: int
    quality_score: float
    schema_profile: SchemaProfile | None
    duplicates: list[DuplicateResult]
    reports: list[ValidationReport]

    @property
    def pass_rate(self) -> float:
        return (self.passed_records / self.total_records * 100) if self.total_records > 0 else 0.0


class ValidationService:
    """Orchestrates validation pipeline for a dataset."""

    def __init__(self):
        self.schema_detector = SchemaDetector()

    def validate_dataset(
        self,
        records: list[dict[str, Any]],
        rules: list[ValidationRule],
        detect_duplicates: bool = True,
        detect_schema: bool = True,
        duplicate_key_fields: list[str] = None,
    ) -> ValidationSummary:
        """Run full validation pipeline on a dataset."""
        reports: list[ValidationReport] = []
        total_errors = 0
        total_warnings = 0

        # Field-level validation
        for idx, record in enumerate(records):
            report = ValidationReport(record_index=idx)
            for rule in rules:
                try:
                    validator = get_validator(rule.rule_type)
                    result = validator.validate(
                        value=record.get(rule.field),
                        field_name=rule.field,
                        **rule.params,
                    )
                    result.severity = rule.severity
                    report.results.append(result)
                    if not result.passed:
                        if rule.severity == Severity.ERROR:
                            total_errors += 1
                        else:
                            total_warnings += 1
                except ValueError as e:
                    logger.warning("unknown_validator", rule=rule.rule_type, error=str(e))

            # Compute quality score per record
            if report.results:
                passed = sum(1 for r in report.results if r.passed)
                report.quality_score = passed / len(report.results) * 100
            reports.append(report)

        passed_records = sum(1 for r in reports if r.passed)
        overall_quality = sum(r.quality_score for r in reports) / len(reports) if reports else 100.0

        # Duplicate detection
        duplicates = []
        if detect_duplicates and records:
            detector = DuplicateDetector(key_fields=duplicate_key_fields)
            duplicates = detector.detect(records)

        # Schema detection
        schema_profile = None
        if detect_schema and records:
            schema_profile = self.schema_detector.detect(records)

        return ValidationSummary(
            total_records=len(records),
            passed_records=passed_records,
            failed_records=len(records) - passed_records,
            total_errors=total_errors,
            total_warnings=total_warnings,
            quality_score=round(overall_quality, 2),
            schema_profile=schema_profile,
            duplicates=duplicates,
            reports=reports,
        )
