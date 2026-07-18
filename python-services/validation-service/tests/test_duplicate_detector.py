"""Unit tests for duplicate detection."""
import pytest
from app.validators.duplicate_detector import DuplicateDetector


class TestDuplicateDetector:
    def test_exact_duplicate_detected(self):
        records = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob",   "email": "bob@example.com"},
            {"name": "Alice", "email": "alice@example.com"},  # duplicate of index 0
        ]
        detector = DuplicateDetector()
        dupes = detector.detect(records)
        assert len(dupes) == 1
        assert dupes[0].record_index == 2
        assert dupes[0].duplicate_of == 0
        assert dupes[0].match_type == "exact"
        assert dupes[0].similarity_score == 100.0

    def test_no_duplicates(self):
        records = [
            {"name": "Alice"},
            {"name": "Bob"},
            {"name": "Charlie"},
        ]
        detector = DuplicateDetector()
        assert detector.detect(records) == []

    def test_key_field_duplicate(self):
        records = [
            {"id": "1", "name": "Alice Smith", "extra": "foo"},
            {"id": "1", "name": "Alice Smith", "extra": "bar"},  # same id+name
        ]
        detector = DuplicateDetector(key_fields=["id", "name"])
        dupes = detector.detect(records)
        assert len(dupes) == 1

    def test_fuzzy_duplicate_detected(self):
        records = [
            {"name": "John Smith",  "email": "john@example.com"},
            {"name": "John Smyth",  "email": "john@example.com"},  # near-duplicate
        ]
        detector = DuplicateDetector(key_fields=["name", "email"], fuzzy_threshold=85)
        dupes = detector.detect(records)
        assert len(dupes) == 1
        assert dupes[0].match_type == "fuzzy"

    def test_empty_records(self):
        detector = DuplicateDetector()
        assert detector.detect([]) == []
