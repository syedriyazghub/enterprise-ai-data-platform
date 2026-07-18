"""
Business Rules Engine

Allows tenants to define, store, and execute custom validation rules
beyond the built-in validators. Rules are stored in Redis and evaluated
at runtime using a simple expression language.

Rule definition example:
    {
        "rule_id": "invoice-amount-positive",
        "name": "Invoice amount must be positive",
        "field": "amount",
        "expression": "value > 0",
        "severity": "error",
        "domain": "financial"
    }
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()

_RULES_KEY_PREFIX = "business_rules:"


@dataclass
class BusinessRule:
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default"
    name: str = ""
    description: str = ""
    field: str = ""
    expression: str = ""        # e.g. "value > 0", "len(value) >= 3"
    severity: str = "error"     # error | warning | info
    domain: str = ""            # financial | healthcare | general
    is_active: bool = True
    tags: list[str] = field(default_factory=list)


@dataclass
class BusinessRuleResult:
    rule_id: str
    rule_name: str
    field: str
    passed: bool
    severity: str
    message: str = ""
    value: Any = None


class BusinessRulesEngine:
    """
    Evaluates custom business rules against records.
    Rules are stored per-tenant in Redis.
    """

    def __init__(self):
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            try:
                import redis as redis_lib
                from app.core.config import settings
                self._redis = redis_lib.from_url(
                    settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2
                )
                self._redis.ping()
            except Exception as exc:
                logger.warning("business_rules_redis_unavailable", error=str(exc))
                self._redis = None
        return self._redis

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def save_rule(self, rule: BusinessRule) -> BusinessRule:
        r = self._get_redis()
        if not r:
            return rule
        key = f"{_RULES_KEY_PREFIX}{rule.tenant_id}:{rule.rule_id}"
        r.set(key, json.dumps(asdict(rule)))
        logger.info("business_rule_saved", rule_id=rule.rule_id, tenant_id=rule.tenant_id)
        return rule

    def get_rule(self, tenant_id: str, rule_id: str) -> BusinessRule | None:
        r = self._get_redis()
        if not r:
            return None
        data = r.get(f"{_RULES_KEY_PREFIX}{tenant_id}:{rule_id}")
        return BusinessRule(**json.loads(data)) if data else None

    def list_rules(self, tenant_id: str, domain: str = "") -> list[BusinessRule]:
        r = self._get_redis()
        if not r:
            return []
        keys = r.keys(f"{_RULES_KEY_PREFIX}{tenant_id}:*")
        rules = []
        for key in keys:
            data = r.get(key)
            if data:
                rule = BusinessRule(**json.loads(data))
                if not domain or rule.domain == domain:
                    rules.append(rule)
        return [rule for rule in rules if rule.is_active]

    def delete_rule(self, tenant_id: str, rule_id: str) -> bool:
        r = self._get_redis()
        if not r:
            return False
        deleted = r.delete(f"{_RULES_KEY_PREFIX}{tenant_id}:{rule_id}")
        return bool(deleted)

    # ── Evaluation ────────────────────────────────────────────────────────────

    def evaluate(
        self,
        records: list[dict[str, Any]],
        rules: list[BusinessRule],
    ) -> list[list[BusinessRuleResult]]:
        """
        Evaluate business rules against all records.
        Returns a list of results per record.
        """
        all_results = []
        for record in records:
            record_results = []
            for rule in rules:
                result = self._evaluate_rule(record, rule)
                record_results.append(result)
            all_results.append(record_results)
        return all_results

    def _evaluate_rule(self, record: dict, rule: BusinessRule) -> BusinessRuleResult:
        value = record.get(rule.field)
        try:
            # Safe evaluation with restricted builtins
            passed = bool(eval(  # noqa: S307
                rule.expression,
                {"__builtins__": {"len": len, "str": str, "int": int, "float": float, "bool": bool}},
                {"value": value, "record": record},
            ))
            return BusinessRuleResult(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                field=rule.field,
                passed=passed,
                severity=rule.severity,
                value=value,
                message="" if passed else f"Rule '{rule.name}' failed for value '{value}'",
            )
        except Exception as exc:
            return BusinessRuleResult(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                field=rule.field,
                passed=False,
                severity=rule.severity,
                value=value,
                message=f"Rule evaluation error: {exc}",
            )
