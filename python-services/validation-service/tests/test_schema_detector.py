"""Unit tests for schema detection."""
import pytest
from app.validators.schema_detector import SchemaDetector


class TestSchemaDetector:
    def setup_method(self):
        self.detector = SchemaDetector()

    def test_detects_string_type(self):
        records = [{"name": "Alice"}, {"name": "Bob"}]
        profile = self.detector.detect(records)
        field = next(f for f in profile.fields if f.name == "name")
        assert field.detected_type == "string"

    def test_detects_integer_type(self):
        records = [{"age": "25"}, {"age": "30"}]
        profile = self.detector.detect(records)
        field = next(f for f in profile.fields if f.name == "age")
        assert field.detected_type == "integer"

    def test_detects_float_type(self):
        records = [{"amount": "99.99"}, {"amount": "150.50"}]
        profile = self.detector.detect(records)
        field = next(f for f in profile.fields if f.name == "amount")
        assert field.detected_type == "float"

    def test_detects_date_type(self):
        records = [{"dob": "2024-01-15"}, {"dob": "2023-06-20"}]
        profile = self.detector.detect(records)
        field = next(f for f in profile.fields if f.name == "dob")
        assert field.detected_type == "date"

    def test_null_count(self):
        records = [{"name": "Alice"}, {"name": None}, {"name": "Bob"}]
        profile = self.detector.detect(records)
        field = next(f for f in profile.fields if f.name == "name")
        assert field.null_count == 1
        assert field.nullable is True

    def test_completeness_score(self):
        records = [{"a": "1", "b": None}, {"a": "2", "b": "x"}]
        profile = self.detector.detect(records)
        assert profile.completeness_score == 75.0

    def test_empty_records(self):
        profile = self.detector.detect([])
        assert profile.record_count == 0
        assert profile.fields == []

    def test_schema_drift_detected(self):
        baseline_records = [{"name": "Alice", "age": "25"}]
        current_records  = [{"name": "Alice", "age": "25", "email": "a@b.com"}]
        baseline = self.detector.detect(baseline_records)
        current  = self.detector.detect(current_records)
        drift = self.detector.detect_drift(baseline, current)
        assert "email" in drift.added_fields
        assert drift.has_drift is True
