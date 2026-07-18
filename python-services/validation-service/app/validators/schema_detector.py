"""Schema detection and drift detection engine."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldSchema:
    name: str
    detected_type: str
    nullable: bool
    sample_values: list[Any] = field(default_factory=list)
    null_count: int = 0
    unique_count: int = 0


@dataclass
class SchemaProfile:
    fields: list[FieldSchema]
    record_count: int
    completeness_score: float


@dataclass
class SchemaDrift:
    added_fields: list[str]
    removed_fields: list[str]
    type_changes: dict[str, tuple[str, str]]  # field -> (old_type, new_type)

    @property
    def has_drift(self) -> bool:
        return bool(self.added_fields or self.removed_fields or self.type_changes)


class SchemaDetector:
    """Automatically detects schema from records and identifies drift."""

    def detect(self, records: list[dict[str, Any]]) -> SchemaProfile:
        if not records:
            return SchemaProfile(fields=[], record_count=0, completeness_score=100.0)

        all_keys = set()
        for r in records:
            all_keys.update(r.keys())

        fields = []
        total_cells = len(records) * len(all_keys)
        null_cells = 0

        for key in sorted(all_keys):
            values = [r.get(key) for r in records]
            non_null = [v for v in values if v is not None and v != ""]
            null_count = len(values) - len(non_null)
            null_cells += null_count

            fields.append(FieldSchema(
                name=key,
                detected_type=self._infer_type(non_null),
                nullable=null_count > 0,
                sample_values=non_null[:3],
                null_count=null_count,
                unique_count=len(set(str(v) for v in non_null)),
            ))

        completeness = ((total_cells - null_cells) / total_cells * 100) if total_cells > 0 else 100.0
        return SchemaProfile(fields=fields, record_count=len(records), completeness_score=round(completeness, 2))

    def detect_drift(self, baseline: SchemaProfile, current: SchemaProfile) -> SchemaDrift:
        baseline_fields = {f.name: f.detected_type for f in baseline.fields}
        current_fields = {f.name: f.detected_type for f in current.fields}

        added = [f for f in current_fields if f not in baseline_fields]
        removed = [f for f in baseline_fields if f not in current_fields]
        type_changes = {
            f: (baseline_fields[f], current_fields[f])
            for f in baseline_fields
            if f in current_fields and baseline_fields[f] != current_fields[f]
        }
        return SchemaDrift(added_fields=added, removed_fields=removed, type_changes=type_changes)

    def _infer_type(self, values: list[Any]) -> str:
        if not values:
            return "unknown"
        import re
        date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}")
        for v in values[:10]:
            s = str(v)
            try:
                int(s)
                return "integer"
            except ValueError:
                pass
            try:
                float(s)
                return "float"
            except ValueError:
                pass
            if date_pattern.match(s):
                return "date"
            if s.lower() in ("true", "false"):
                return "boolean"
        return "string"
