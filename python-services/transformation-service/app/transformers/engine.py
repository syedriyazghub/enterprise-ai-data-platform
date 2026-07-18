"""
Data Transformation Engine

Supports:
- Field mapping & renaming
- Type casting
- String normalization
- Date formatting
- PII masking
- Data enrichment
- Custom expression evaluation
- Aggregations
"""
import re
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
import structlog

logger = structlog.get_logger()


class TransformationType(str, Enum):
    RENAME = "rename"
    CAST = "cast"
    NORMALIZE = "normalize"
    MASK_PII = "mask_pii"
    DATE_FORMAT = "date_format"
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"
    TRIM = "trim"
    REPLACE = "replace"
    SPLIT = "split"
    CONCAT = "concat"
    MATH = "math"
    CONDITIONAL = "conditional"
    DROP = "drop"
    DEFAULT = "default"
    HASH = "hash"


@dataclass
class TransformationRule:
    transformation_type: TransformationType
    source_field: str
    target_field: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class TransformationResult:
    records: list[dict[str, Any]]
    rules_applied: int
    records_transformed: int
    errors: list[dict]


class TransformationEngine:
    """Applies a pipeline of transformation rules to records."""

    def transform(
        self,
        records: list[dict[str, Any]],
        rules: list[TransformationRule],
    ) -> TransformationResult:
        transformed = [dict(r) for r in records]
        errors = []

        for rule in rules:
            for idx, record in enumerate(transformed):
                try:
                    transformed[idx] = self._apply_rule(record, rule)
                except Exception as e:
                    errors.append({"record_index": idx, "rule": rule.transformation_type, "error": str(e)})

        return TransformationResult(
            records=transformed,
            rules_applied=len(rules),
            records_transformed=len(transformed),
            errors=errors,
        )

    def _apply_rule(self, record: dict, rule: TransformationRule) -> dict:
        t = rule.transformation_type
        src = rule.source_field
        tgt = rule.target_field or src
        val = record.get(src)

        if t == TransformationType.RENAME:
            record[tgt] = record.pop(src, None)

        elif t == TransformationType.CAST:
            target_type = rule.params.get("type", "str")
            record[tgt] = self._cast(val, target_type)

        elif t == TransformationType.NORMALIZE:
            if val is not None:
                record[tgt] = re.sub(r"\s+", " ", str(val)).strip()

        elif t == TransformationType.MASK_PII:
            record[tgt] = self._mask(val, rule.params.get("mask_type", "partial"))

        elif t == TransformationType.DATE_FORMAT:
            record[tgt] = self._reformat_date(val, rule.params.get("from_format"), rule.params.get("to_format"))

        elif t == TransformationType.UPPERCASE:
            record[tgt] = str(val).upper() if val is not None else val

        elif t == TransformationType.LOWERCASE:
            record[tgt] = str(val).lower() if val is not None else val

        elif t == TransformationType.TRIM:
            record[tgt] = str(val).strip() if val is not None else val

        elif t == TransformationType.REPLACE:
            if val is not None:
                record[tgt] = str(val).replace(rule.params.get("find", ""), rule.params.get("replace", ""))

        elif t == TransformationType.CONCAT:
            fields = rule.params.get("fields", [src])
            sep = rule.params.get("separator", " ")
            record[tgt] = sep.join(str(record.get(f, "")) for f in fields)

        elif t == TransformationType.DROP:
            record.pop(src, None)

        elif t == TransformationType.DEFAULT:
            if record.get(src) is None or record.get(src) == "":
                record[tgt] = rule.params.get("value")

        elif t == TransformationType.HASH:
            if val is not None:
                record[tgt] = hashlib.sha256(str(val).encode()).hexdigest()

        return record

    def _cast(self, value: Any, target_type: str) -> Any:
        if value is None:
            return None
        type_map = {"int": int, "float": float, "str": str, "bool": bool}
        cast_fn = type_map.get(target_type, str)
        return cast_fn(value)

    def _mask(self, value: Any, mask_type: str) -> str:
        if value is None:
            return None
        s = str(value)
        if mask_type == "full":
            return "*" * len(s)
        elif mask_type == "partial":
            visible = max(2, len(s) // 4)
            return s[:visible] + "*" * (len(s) - visible)
        elif mask_type == "email":
            parts = s.split("@")
            if len(parts) == 2:
                return parts[0][:2] + "***@" + parts[1]
        return "***"

    def _reformat_date(self, value: Any, from_format: str, to_format: str) -> str:
        if value is None:
            return None
        from datetime import datetime
        try:
            dt = datetime.strptime(str(value), from_format)
            return dt.strftime(to_format)
        except ValueError:
            return str(value)
