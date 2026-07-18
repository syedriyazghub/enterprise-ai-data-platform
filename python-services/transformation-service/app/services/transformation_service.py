"""
Transformation orchestration service.

Wraps the TransformationEngine with:
- Job tracking (in-memory for stateless service, Redis for persistence)
- Event publishing on start/complete
- Rule validation before execution
- Metrics logging
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.transformers.engine import TransformationEngine, TransformationRule, TransformationType

logger = structlog.get_logger()


@dataclass
class TransformationJob:
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"          # pending | running | completed | failed
    rules_applied: int = 0
    records_in: int = 0
    records_out: int = 0
    errors: list[dict] = field(default_factory=list)
    duration_ms: float = 0.0
    error_message: str = ""


class TransformationService:
    """Orchestrates transformation pipeline execution."""

    def __init__(self):
        self._engine = TransformationEngine()

    def transform(
        self,
        records: list[dict[str, Any]],
        rules: list[dict[str, Any]],
        tenant_id: str = "default",
    ) -> TransformationJob:
        """
        Apply transformation rules to records.

        Args:
            records: List of input records.
            rules: List of rule dicts with keys:
                   transformation_type, source_field, target_field, params.
            tenant_id: Tenant identifier for logging.

        Returns:
            TransformationJob with results and metadata.
        """
        job = TransformationJob(records_in=len(records))
        t0 = time.monotonic()

        try:
            parsed_rules = self._parse_rules(rules)
            result = self._engine.transform(records, parsed_rules)

            job.status = "completed"
            job.rules_applied = result.rules_applied
            job.records_out = result.records_transformed
            job.errors = result.errors
            job.duration_ms = round((time.monotonic() - t0) * 1000, 2)

            logger.info(
                "transformation_completed",
                job_id=job.job_id,
                tenant_id=tenant_id,
                records_in=job.records_in,
                records_out=job.records_out,
                rules=job.rules_applied,
                errors=len(job.errors),
                duration_ms=job.duration_ms,
            )
            return job, result.records

        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.duration_ms = round((time.monotonic() - t0) * 1000, 2)
            logger.error("transformation_failed", job_id=job.job_id, error=str(exc))
            raise

    def _parse_rules(self, rules: list[dict[str, Any]]) -> list[TransformationRule]:
        parsed = []
        for r in rules:
            try:
                parsed.append(TransformationRule(
                    transformation_type=TransformationType(r["transformation_type"]),
                    source_field=r["source_field"],
                    target_field=r.get("target_field"),
                    params=r.get("params", {}),
                ))
            except (KeyError, ValueError) as exc:
                raise ValueError(f"Invalid rule {r}: {exc}") from exc
        return parsed

    def list_transformation_types(self) -> list[dict[str, str]]:
        """Return all available transformation types with descriptions."""
        descriptions = {
            TransformationType.RENAME:      "Rename a field",
            TransformationType.CAST:        "Cast field to int/float/str/bool",
            TransformationType.NORMALIZE:   "Trim and collapse whitespace",
            TransformationType.MASK_PII:    "Mask PII (full/partial/email)",
            TransformationType.DATE_FORMAT: "Reformat date strings",
            TransformationType.UPPERCASE:   "Convert to uppercase",
            TransformationType.LOWERCASE:   "Convert to lowercase",
            TransformationType.TRIM:        "Strip leading/trailing whitespace",
            TransformationType.REPLACE:     "Find and replace substring",
            TransformationType.SPLIT:       "Split string into list",
            TransformationType.CONCAT:      "Concatenate multiple fields",
            TransformationType.MATH:        "Apply arithmetic expression",
            TransformationType.CONDITIONAL: "Conditional value assignment",
            TransformationType.DROP:        "Remove a field",
            TransformationType.DEFAULT:     "Set default value if null/empty",
            TransformationType.HASH:        "SHA-256 hash a field value",
        }
        return [
            {"type": t.value, "description": descriptions.get(t, t.value)}
            for t in TransformationType
        ]
