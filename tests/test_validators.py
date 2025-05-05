"""
Testy dla modułu validators.
"""
import pytest
from osint_super_kombajn.utils.validators import validate_email

def test_validate_email_valid():
    """Test walidacji poprawnego adresu e-mail."""
    assert validate_email("test@example.com") is True

def test_validate_email_invalid():
    """Test walidacji niepoprawnego adresu e-mail."""
    assert validate_email("testexample.com") is False
    assert validate_email("test@") is False
    assert validate_email("@example.com") is False

def test_validate_email_empty():
    """Test walidacji pustego adresu e-mail."""
    assert validate_email("") is False
