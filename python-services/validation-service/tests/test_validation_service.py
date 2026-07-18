"""
Comprehensive tests for ValidationService, DuplicateDetector,
SchemaDetector, and BusinessRulesEngine.
"""
import pytest
from app.services.validation_service import ValidationService, ValidationRule
from app.validators.core_validators import Severity
from app.validators.duplicate_detector import DuplicateDetector
from app.validators.schema_detector import SchemaDetector


# ── ValidationService ─────────────────────────────────────────────────────────

class TestValidationService:
    def setup_method(self):
        self.service = ValidationService()

    def _make_records(self):
        return [
            {"email": "alice@example.com", "age": "25", "pan": "ABCDE1234F"},
            {"email": "not-an-email",       "age": "200", "pan": "INVALID"},
            {"email": None,                 "age": "30",  "pan": "FGHIJ5678K"},
        ]

    def _make_rules(self):
        return [
            ValidationRule(field="email", rule_type="email",         severity=Severity.ERROR),
            ValidationRule(field="email", rule_type="not_null",      severity=Severity.ERROR),
            ValidationRule(field="age",   rule_type="numeric_range", severity=Severity.WARNING, params={"min": 0, "max": 150}),
            ValidationRule(field="pan",   rule_type="pan",           severity=Severity.ERROR),
        ]

    def test_returns_summary(self):
        summary = self.service.validate_dataset(self._make_records(), self._make_rules())
        assert summary.total_records == 3

    def test_quality_score_between_0_and_100(self):
        summary = self.service.validate_dataset(self._make_records(), self._make_rules())
        assert 0.0 <= summary.quality_score <= 100.0

    def test_failed_records_counted(self):
        summary = self.service.validate_dataset(self._make_records(), self._make_rules())
        assert summary.failed_records > 0

    def test_pass_rate_calculation(self):
        summary = self.service.validate_dataset(self._make_records(), self._make_rules())
        expected = summary.passed_records / summary.total_records * 100
        assert abs(summary.pass_rate - expected) < 0.01

    def test_all_pass_with_valid_data(self):
        records = [{"email": "a@b.com", "age": "25"}]
        rules = [
            ValidationRule(field="email", rule_type="email",         severity=Severity.ERROR),
            ValidationRule(field="age",   rule_type="numeric_range", severity=Severity.ERROR, params={"min": 0, "max": 150}),
        ]
        summary = self.service.validate_dataset(records, rules)
        assert summary.passed_records == 1
        assert summary.total_errors == 0

    def test_schema_detection_enabled(self):
        summary = self.service.validate_dataset(self._make_records(), self._make_rules(), detect_schema=True)
        assert summary.schema_profile is not None
        assert len(summary.schema_profile.fields) > 0

    def test_schema_detection_disabled(self):
        summary = self.service.validate_dataset(self._make_records(), self._make_rules(), detect_schema=False)
        assert summary.schema_profile is None

    def test_duplicate_detection_enabled(self):
        records = [
            {"id": "1", "name": "Alice"},
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"},
        ]
        summary = self.service.validate_dataset(records, [], detect_duplicates=True, duplicate_key_fields=["id"])
        assert len(summary.duplicates) >= 1

    def test_duplicate_detection_disabled(self):
        records = [{"id": "1"}, {"id": "1"}]
        summary = self.service.validate_dataset(records, [], detect_duplicates=False)
        assert summary.duplicates == []

    def test_unknown_validator_skipped(self):
        records = [{"field": "value"}]
        rules = [ValidationRule(field="field", rule_type="nonexistent_validator")]
        # Should not raise, just skip unknown validators
        summary = self.service.validate_dataset(records, rules)
        assert summary.total_records == 1

    def test_empty_records_returns_100_quality(self):
        # Edge case: empty dataset
        summary = self.service.validate_dataset([], [])
        assert summary.total_records == 0
        assert summary.quality_score == 100.0


# ── DuplicateDetector ─────────────────────────────────────────────────────────

class TestDuplicateDetector:
    def test_exact_duplicate_detected(self):
        records = [{"id": "1", "name": "Alice"}, {"id": "1", "name": "Alice"}]
        detector = DuplicateDetector()
        dupes = detector.detect(records)
        assert len(dupes) == 1
        assert dupes[0].match_type == "exact"
        assert dupes[0].similarity_score == 100.0

    def test_no_duplicates(self):
        records = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        detector = DuplicateDetector()
        assert detector.detect(records) == []

    def test_key_fields_subset(self):
        records = [
            {"id": "1", "name": "Alice", "extra": "x"},
            {"id": "1", "name": "Alice", "extra": "y"},
        ]
        detector = DuplicateDetector(key_fields=["id", "name"])
        dupes = detector.detect(records)
        assert len(dupes) == 1

    def test_fuzzy_duplicate_detected(self):
        records = [
            {"name": "John Smith", "email": "john@example.com"},
            {"name": "John Smyth", "email": "john@example.com"},
        ]
        detector = DuplicateDetector(fuzzy_threshold=80)
        dupes = detector.detect(records)
        assert len(dupes) >= 1
        assert dupes[0].match_type == "fuzzy"

    def test_single_record_no_duplicates(self):
        records = [{"id": "1"}]
        detector = DuplicateDetector()
        assert detector.detect(records) == []

    def test_empty_records(self):
        detector = DuplicateDetector()
        assert detector.detect([]) == []


# ── SchemaDetector ────────────────────────────────────────────────────────────

class TestSchemaDetector:
    def setup_method(self):
        self.detector = SchemaDetector()

    def test_detects_string_type(self):
        records = [{"name": "Alice"}, {"name": "Bob"}]
        profile = self.detector.detect(records)
        name_field = next(f for f in profile.fields if f.name == "name")
        assert name_field.detected_type == "string"

    def test_detects_integer_type(self):
        records = [{"age": "25"}, {"age": "30"}]
        profile = self.detector.detect(records)
        age_field = next(f for f in profile.fields if f.name == "age")
        assert age_field.detected_type == "integer"

    def test_detects_float_type(self):
        records = [{"amount": "19.99"}, {"amount": "5.50"}]
        profile = self.detector.detect(records)
        amount_field = next(f for f in profile.fields if f.name == "amount")
        assert amount_field.detected_type == "float"

    def test_detects_date_type(self):
        records = [{"dob": "2000-01-15"}, {"dob": "1990-06-20"}]
        profile = self.detector.detect(records)
        dob_field = next(f for f in profile.fields if f.name == "dob")
        assert dob_field.detected_type == "date"

    def test_nullable_field_detected(self):
        records = [{"name": "Alice"}, {"name": None}]
        profile = self.detector.detect(records)
        name_field = next(f for f in profile.fields if f.name == "name")
        assert name_field.nullable is True

    def test_completeness_score_100_when_no_nulls(self):
        records = [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
        profile = self.detector.detect(records)
        assert profile.completeness_score == 100.0

    def test_completeness_score_below_100_with_nulls(self):
        records = [{"a": "1", "b": None}, {"a": "2", "b": "3"}]
        profile = self.detector.detect(records)
        assert profile.completeness_score < 100.0

    def test_empty_records(self):
        profile = self.detector.detect([])
        assert profile.fields == []
        assert profile.record_count == 0

    def test_schema_drift_detection(self):
        baseline_records = [{"id": "1", "name": "Alice"}]
        current_records  = [{"id": "1", "name": "Alice", "email": "a@b.com"}]
        baseline = self.detector.detect(baseline_records)
        current  = self.detector.detect(current_records)
        drift = self.detector.detect_drift(baseline, current)
        assert "email" in drift.added_fields
        assert drift.has_drift is True

    def test_no_drift_same_schema(self):
        records = [{"id": "1", "name": "Alice"}]
        baseline = self.detector.detect(records)
        current  = self.detector.detect(records)
        drift = self.detector.detect_drift(baseline, current)
        assert drift.has_drift is False
