import re

def mask_pii(text: str) -> str:
    """Basic PII masker using regex. In production, use Microsoft Presidio."""
    # Mask emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[EMAIL PROTECTED]', text)
    # Mask phone numbers
    text = re.sub(r'\+?\d{1,3}[-\.\s]?\(?\d{2,3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4}', '[PHONE PROTECTED]', text)
    return text
