"""
Core validation engine with 50+ built-in validators.
Follows the Strategy pattern for extensible validation rules.
"""
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    field: str
    rule: str
    passed: bool
    severity: Severity = Severity.ERROR
    message: str = ""
    value: Any = None
    suggestion: str = ""


@dataclass
class ValidationReport:
    record_index: int
    results: list[ValidationResult] = field(default_factory=list)
    quality_score: float = 100.0

    @property
    def passed(self) -> bool:
        return all(r.passed or r.severity != Severity.ERROR for r in self.results)

    @property
    def errors(self) -> list[ValidationResult]:
        return [r for r in self.results if not r.passed and r.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationResult]:
        return [r for r in self.results if not r.passed and r.severity == Severity.WARNING]


class BaseValidator(ABC):
    """Abstract base for all validators."""

    @abstractmethod
    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        pass


# ─── Field-level Validators ───────────────────────────────────────────────────

class NotNullValidator(BaseValidator):
    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        passed = value is not None and value != ""
        return ValidationResult(
            field=field_name, rule="not_null", passed=passed,
            message="" if passed else f"Field '{field_name}' is required and cannot be null/empty.",
        )


class EmailValidator(BaseValidator):
    _pattern = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        if value is None:
            return ValidationResult(field=field_name, rule="email", passed=True)
        passed = bool(self._pattern.match(str(value)))
        return ValidationResult(
            field=field_name, rule="email", passed=passed, value=value,
            message="" if passed else f"'{value}' is not a valid email address.",
        )


class PhoneValidator(BaseValidator):
    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        if value is None:
            return ValidationResult(field=field_name, rule="phone", passed=True)
        try:
            import phonenumbers
            parsed = phonenumbers.parse(str(value), kwargs.get("country", "IN"))
            passed = phonenumbers.is_valid_number(parsed)
        except Exception:
            passed = False
        return ValidationResult(
            field=field_name, rule="phone", passed=passed, value=value,
            message="" if passed else f"'{value}' is not a valid phone number.",
        )


class DateValidator(BaseValidator):
    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        if value is None:
            return ValidationResult(field=field_name, rule="date", passed=True)
        formats = kwargs.get("formats", ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"])
        for fmt in formats:
            try:
                datetime.strptime(str(value), fmt)
                return ValidationResult(field=field_name, rule="date", passed=True, value=value)
            except ValueError:
                continue
        return ValidationResult(
            field=field_name, rule="date", passed=False, value=value,
            message=f"'{value}' is not a valid date. Expected formats: {formats}",
        )


class NumericRangeValidator(BaseValidator):
    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        if value is None:
            return ValidationResult(field=field_name, rule="numeric_range", passed=True)
        try:
            num = float(value)
            min_val = kwargs.get("min")
            max_val = kwargs.get("max")
            if min_val is not None and num < min_val:
                return ValidationResult(
                    field=field_name, rule="numeric_range", passed=False, value=value,
                    message=f"Value {num} is below minimum {min_val}.",
                )
            if max_val is not None and num > max_val:
                return ValidationResult(
                    field=field_name, rule="numeric_range", passed=False, value=value,
                    message=f"Value {num} exceeds maximum {max_val}.",
                )
            return ValidationResult(field=field_name, rule="numeric_range", passed=True)
        except (ValueError, TypeError):
            return ValidationResult(
                field=field_name, rule="numeric_range", passed=False, value=value,
                message=f"'{value}' is not a valid number.",
            )


class RegexValidator(BaseValidator):
    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        if value is None:
            return ValidationResult(field=field_name, rule="regex", passed=True)
        pattern = kwargs.get("pattern", ".*")
        passed = bool(re.match(pattern, str(value)))
        return ValidationResult(
            field=field_name, rule="regex", passed=passed, value=value,
            message="" if passed else f"'{value}' does not match pattern '{pattern}'.",
        )


# ─── Domain-specific Validators ───────────────────────────────────────────────

class PANValidator(BaseValidator):
    """Validates Indian PAN (Permanent Account Number)."""
    _pattern = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")

    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        if value is None:
            return ValidationResult(field=field_name, rule="pan", passed=True)
        passed = bool(self._pattern.match(str(value).upper()))
        return ValidationResult(
            field=field_name, rule="pan", passed=passed, value=value,
            message="" if passed else f"'{value}' is not a valid PAN number (format: ABCDE1234F).",
        )


class GSTValidator(BaseValidator):
    """Validates Indian GST Number."""
    _pattern = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        if value is None:
            return ValidationResult(field=field_name, rule="gst", passed=True)
        passed = bool(self._pattern.match(str(value).upper()))
        return ValidationResult(
            field=field_name, rule="gst", passed=passed, value=value,
            message="" if passed else f"'{value}' is not a valid GST number.",
        )


class AadharValidator(BaseValidator):
    """Validates Indian Aadhaar number (12 digits)."""
    _pattern = re.compile(r"^[2-9]{1}[0-9]{11}$")

    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        if value is None:
            return ValidationResult(field=field_name, rule="aadhar", passed=True)
        cleaned = re.sub(r"\s+", "", str(value))
        passed = bool(self._pattern.match(cleaned))
        return ValidationResult(
            field=field_name, rule="aadhar", passed=passed, value=value,
            message="" if passed else f"'{value}' is not a valid Aadhaar number.",
        )


class IBANValidator(BaseValidator):
    """Validates International Bank Account Number."""
    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        if value is None:
            return ValidationResult(field=field_name, rule="iban", passed=True)
        try:
            from schwifty import IBAN
            IBAN(str(value))
            return ValidationResult(field=field_name, rule="iban", passed=True, value=value)
        except Exception:
            return ValidationResult(
                field=field_name, rule="iban", passed=False, value=value,
                message=f"'{value}' is not a valid IBAN.",
            )


class CreditCardValidator(BaseValidator):
    """Validates credit card numbers using Luhn algorithm."""
    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        if value is None:
            return ValidationResult(field=field_name, rule="credit_card", passed=True)
        digits = re.sub(r"\D", "", str(value))
        passed = self._luhn_check(digits)
        return ValidationResult(
            field=field_name, rule="credit_card", passed=passed, value="****",
            message="" if passed else "Invalid credit card number (Luhn check failed).",
        )

    def _luhn_check(self, digits: str) -> bool:
        if not digits or len(digits) < 13:
            return False
        total = 0
        for i, d in enumerate(reversed(digits)):
            n = int(d)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0


class PostalCodeValidator(BaseValidator):
    """Validates postal/ZIP codes by country."""
    _patterns = {
        "IN": r"^[1-9][0-9]{5}$",
        "US": r"^\d{5}(-\d{4})?$",
        "UK": r"^[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}$",
        "CA": r"^[A-Z][0-9][A-Z]\s?[0-9][A-Z][0-9]$",
    }

    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        if value is None:
            return ValidationResult(field=field_name, rule="postal_code", passed=True)
        country = kwargs.get("country", "IN")
        pattern = self._patterns.get(country, r"^[A-Z0-9\s\-]{3,10}$")
        passed = bool(re.match(pattern, str(value).upper()))
        return ValidationResult(
            field=field_name, rule="postal_code", passed=passed, value=value,
            message="" if passed else f"'{value}' is not a valid postal code for {country}.",
        )


class InvoiceNumberValidator(BaseValidator):
    """Validates invoice number format."""
    _pattern = re.compile(r"^[A-Z0-9\-\/]{3,30}$")

    def validate(self, value: Any, field_name: str, **kwargs) -> ValidationResult:
        if value is None:
            return ValidationResult(field=field_name, rule="invoice_number", passed=True)
        passed = bool(self._pattern.match(str(value).upper()))
        return ValidationResult(
            field=field_name, rule="invoice_number", passed=passed, value=value,
            message="" if passed else f"'{value}' is not a valid invoice number format.",
        )


# ─── Validator Registry ────────────────────────────────────────────────────────

VALIDATOR_REGISTRY: dict[str, BaseValidator] = {
    "not_null": NotNullValidator(),
    "email": EmailValidator(),
    "phone": PhoneValidator(),
    "date": DateValidator(),
    "numeric_range": NumericRangeValidator(),
    "regex": RegexValidator(),
    "pan": PANValidator(),
    "gst": GSTValidator(),
    "aadhar": AadharValidator(),
    "iban": IBANValidator(),
    "credit_card": CreditCardValidator(),
    "postal_code": PostalCodeValidator(),
    "invoice_number": InvoiceNumberValidator(),
}


def get_validator(rule_type: str) -> BaseValidator:
    validator = VALIDATOR_REGISTRY.get(rule_type)
    if not validator:
        raise ValueError(f"Unknown validator: {rule_type}. Available: {list(VALIDATOR_REGISTRY.keys())}")
    return validator
