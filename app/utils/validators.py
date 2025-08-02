import re

def is_valid_email(email: str) -> bool:
    """Basit email regex kontrolü yapar."""
    if not email:
        return False
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(email_regex, email) is not None

def is_strong_password(password: str) -> bool:
    """
    Şifre güçlü mü diye kontrol eder:
    - En az 8 karakter
    - En az 1 büyük harf
    - En az 1 küçük harf
    - En az 1 rakam
    - En az 1 özel karakter
    """
    if not password or len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True
