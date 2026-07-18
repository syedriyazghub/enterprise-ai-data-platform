"""Duplicate detection using exact match and fuzzy matching."""
from dataclasses import dataclass, field
from typing import Any
import hashlib
import json
from fuzzywuzzy import fuzz


@dataclass
class DuplicateResult:
    record_index: int
    duplicate_of: int
    similarity_score: float
    match_type: str  # "exact" | "fuzzy"
    matched_fields: list[str]


class DuplicateDetector:
    """
    Detects duplicate records using:
    - Exact hash matching for identical records
    - Fuzzy matching for near-duplicates
    """

    def __init__(self, key_fields: list[str] = None, fuzzy_threshold: int = 90):
        self.key_fields = key_fields
        self.fuzzy_threshold = fuzzy_threshold

    def detect(self, records: list[dict[str, Any]]) -> list[DuplicateResult]:
        """Find duplicates in a list of records."""
        duplicates = []
        seen_hashes: dict[str, int] = {}
        seen_records: list[tuple[int, dict]] = []

        for idx, record in enumerate(records):
            # Exact match via hash
            record_hash = self._hash_record(record)
            if record_hash in seen_hashes:
                duplicates.append(DuplicateResult(
                    record_index=idx,
                    duplicate_of=seen_hashes[record_hash],
                    similarity_score=100.0,
                    match_type="exact",
                    matched_fields=list(record.keys()),
                ))
                continue

            # Fuzzy match
            fuzzy_dup = self._fuzzy_match(idx, record, seen_records)
            if fuzzy_dup:
                duplicates.append(fuzzy_dup)
            else:
                seen_hashes[record_hash] = idx
                seen_records.append((idx, record))

        return duplicates

    def _hash_record(self, record: dict) -> str:
        if self.key_fields:
            subset = {k: record.get(k) for k in self.key_fields}
        else:
            subset = record
        content = json.dumps(subset, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()

    def _fuzzy_match(self, idx: int, record: dict, seen: list) -> DuplicateResult | None:
        fields = self.key_fields or list(record.keys())
        record_str = " ".join(str(record.get(f, "")) for f in fields)

        for prev_idx, prev_record in seen:
            prev_str = " ".join(str(prev_record.get(f, "")) for f in fields)
            score = fuzz.token_sort_ratio(record_str, prev_str)
            if score >= self.fuzzy_threshold:
                return DuplicateResult(
                    record_index=idx,
                    duplicate_of=prev_idx,
                    similarity_score=float(score),
                    match_type="fuzzy",
                    matched_fields=fields,
                )
        return None
