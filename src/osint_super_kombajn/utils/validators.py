"""
Walidatory danych OSINT.
"""
import re

def validate_email(email):
    """
    Waliduje adres e-mail.
    
    Args:
        email: Adres e-mail do walidacji
        
    Returns:
        True jeśli adres e-mail jest poprawny, False w przeciwnym razie
    """
    if not email:
        return False
    
    # Prosty wzorzec dla adresu e-mail
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
