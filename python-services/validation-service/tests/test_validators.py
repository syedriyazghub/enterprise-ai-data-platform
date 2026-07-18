"""Unit tests for validation service core validators."""
import pytest
from app.validators.core_validators import (
    EmailValidator, PhoneValidator, PANValidator, GSTValidator,
    AadharValidator, CreditCardValidator, PostalCodeValidator,
    NotNullValidator, DateValidator, NumericRangeValidator,
)


class TestNotNullValidator:
    def setup_method(self):
        self.v = NotNullValidator()

    def test_passes_with_value(self):
        assert self.v.validate("hello", "field").passed is True

    def test_fails_with_none(self):
        assert self.v.validate(None, "field").passed is False

    def test_fails_with_empty_string(self):
        assert self.v.validate("", "field").passed is False

    def test_passes_with_zero(self):
        assert self.v.validate(0, "field").passed is True


class TestEmailValidator:
    def setup_method(self):
        self.v = EmailValidator()

    def test_valid_email(self):
        assert self.v.validate("user@example.com", "email").passed is True

    def test_invalid_email_no_at(self):
        assert self.v.validate("userexample.com", "email").passed is False

    def test_invalid_email_no_domain(self):
        assert self.v.validate("user@", "email").passed is False

    def test_none_passes(self):
        assert self.v.validate(None, "email").passed is True

    def test_subdomain_email(self):
        assert self.v.validate("user@mail.example.co.uk", "email").passed is True


class TestPANValidator:
    def setup_method(self):
        self.v = PANValidator()

    def test_valid_pan(self):
        assert self.v.validate("ABCDE1234F", "pan").passed is True

    def test_invalid_pan_short(self):
        assert self.v.validate("ABCD1234F", "pan").passed is False

    def test_invalid_pan_wrong_format(self):
        assert self.v.validate("12345ABCDE", "pan").passed is False

    def test_lowercase_pan_passes(self):
        assert self.v.validate("abcde1234f", "pan").passed is True


class TestGSTValidator:
    def setup_method(self):
        self.v = GSTValidator()

    def test_valid_gst(self):
        assert self.v.validate("27ABCDE1234F1Z5", "gst").passed is True

    def test_invalid_gst(self):
        assert self.v.validate("INVALID_GST", "gst").passed is False


class TestCreditCardValidator:
    def setup_method(self):
        self.v = CreditCardValidator()

    def test_valid_visa(self):
        assert self.v.validate("4532015112830366", "card").passed is True

    def test_valid_mastercard(self):
        assert self.v.validate("5425233430109903", "card").passed is True

    def test_invalid_card(self):
        assert self.v.validate("1234567890123456", "card").passed is False

    def test_card_with_spaces(self):
        assert self.v.validate("4532 0151 1283 0366", "card").passed is True


class TestDateValidator:
    def setup_method(self):
        self.v = DateValidator()

    def test_valid_iso_date(self):
        assert self.v.validate("2024-01-15", "date").passed is True

    def test_valid_dd_mm_yyyy(self):
        assert self.v.validate("15/01/2024", "date").passed is True

    def test_invalid_date(self):
        assert self.v.validate("not-a-date", "date").passed is False

    def test_none_passes(self):
        assert self.v.validate(None, "date").passed is True


class TestNumericRangeValidator:
    def setup_method(self):
        self.v = NumericRangeValidator()

    def test_within_range(self):
        assert self.v.validate(50, "age", min=0, max=120).passed is True

    def test_below_min(self):
        assert self.v.validate(-1, "age", min=0).passed is False

    def test_above_max(self):
        assert self.v.validate(200, "age", max=120).passed is False

    def test_non_numeric(self):
        assert self.v.validate("abc", "amount").passed is False
