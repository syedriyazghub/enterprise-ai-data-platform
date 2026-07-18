"""Unit tests for transformation engine."""
import pytest
from app.transformers.engine import TransformationEngine, TransformationRule, TransformationType


class TestTransformationEngine:
    def setup_method(self):
        self.engine = TransformationEngine()

    def _run(self, records, rules):
        return self.engine.transform(records, rules).records

    def test_rename(self):
        result = self._run(
            [{"first_name": "Alice"}],
            [TransformationRule(TransformationType.RENAME, "first_name", "name")]
        )
        assert "name" in result[0]
        assert "first_name" not in result[0]

    def test_uppercase(self):
        result = self._run(
            [{"city": "london"}],
            [TransformationRule(TransformationType.UPPERCASE, "city")]
        )
        assert result[0]["city"] == "LONDON"

    def test_lowercase(self):
        result = self._run(
            [{"status": "ACTIVE"}],
            [TransformationRule(TransformationType.LOWERCASE, "status")]
        )
        assert result[0]["status"] == "active"

    def test_trim(self):
        result = self._run(
            [{"name": "  Alice  "}],
            [TransformationRule(TransformationType.TRIM, "name")]
        )
        assert result[0]["name"] == "Alice"

    def test_cast_to_int(self):
        result = self._run(
            [{"age": "25"}],
            [TransformationRule(TransformationType.CAST, "age", params={"type": "int"})]
        )
        assert result[0]["age"] == 25
        assert isinstance(result[0]["age"], int)

    def test_mask_pii_partial(self):
        result = self._run(
            [{"phone": "9876543210"}],
            [TransformationRule(TransformationType.MASK_PII, "phone", params={"mask_type": "partial"})]
        )
        assert result[0]["phone"].endswith("*" * 7)

    def test_mask_pii_full(self):
        result = self._run(
            [{"ssn": "123-45-6789"}],
            [TransformationRule(TransformationType.MASK_PII, "ssn", params={"mask_type": "full"})]
        )
        assert all(c == "*" for c in result[0]["ssn"])

    def test_hash(self):
        result = self._run(
            [{"email": "alice@example.com"}],
            [TransformationRule(TransformationType.HASH, "email")]
        )
        assert len(result[0]["email"]) == 64  # SHA-256 hex

    def test_default_value(self):
        result = self._run(
            [{"status": None}],
            [TransformationRule(TransformationType.DEFAULT, "status", params={"value": "active"})]
        )
        assert result[0]["status"] == "active"

    def test_concat(self):
        result = self._run(
            [{"first": "John", "last": "Doe"}],
            [TransformationRule(TransformationType.CONCAT, "first", "full_name",
                                params={"fields": ["first", "last"], "separator": " "})]
        )
        assert result[0]["full_name"] == "John Doe"

    def test_replace(self):
        result = self._run(
            [{"text": "hello world"}],
            [TransformationRule(TransformationType.REPLACE, "text",
                                params={"find": "world", "replace": "earth"})]
        )
        assert result[0]["text"] == "hello earth"

    def test_drop(self):
        result = self._run(
            [{"keep": "yes", "remove": "no"}],
            [TransformationRule(TransformationType.DROP, "remove")]
        )
        assert "remove" not in result[0]
        assert "keep" in result[0]

    def test_date_format(self):
        result = self._run(
            [{"dob": "2024-01-15"}],
            [TransformationRule(TransformationType.DATE_FORMAT, "dob",
                                params={"from_format": "%Y-%m-%d", "to_format": "%d/%m/%Y"})]
        )
        assert result[0]["dob"] == "15/01/2024"

    def test_multiple_rules_applied_in_order(self):
        result = self._run(
            [{"name": "  alice  "}],
            [
                TransformationRule(TransformationType.TRIM, "name"),
                TransformationRule(TransformationType.UPPERCASE, "name"),
            ]
        )
        assert result[0]["name"] == "ALICE"
