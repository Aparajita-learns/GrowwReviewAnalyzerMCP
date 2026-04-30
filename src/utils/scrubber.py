import re

class PIIScrubber:
    """
    Simple PII Scrubber using regex to mask common sensitive patterns.
    Can be extended with LLM-based entities in later phases.
    """
    
    # Regex patterns for common PII
    PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        'card': r'\b(?:\d[ -]*?){13,16}\b', # Simple 13-16 digit numbers
    }

    def scrub(self, text: str) -> str:
        if not text:
            return text
        
        scrubbed_text = text
        
        # Mask emails
        scrubbed_text = re.sub(self.PATTERNS['email'], '[EMAIL_REDACTED]', scrubbed_text)
        
        # Mask phone numbers
        scrubbed_text = re.sub(self.PATTERNS['phone'], '[PHONE_REDACTED]', scrubbed_text)
        
        # Mask credit cards
        scrubbed_text = re.sub(self.PATTERNS['card'], '[CARD_REDACTED]', scrubbed_text)
        
        return scrubbed_text

if __name__ == "__main__":
    scrubber = PIIScrubber()
    test_text = "Contact me at user@example.com or call 123-456-7890. My card is 1234-5678-9012-3456."
    print(f"Original: {test_text}")
    print(f"Scrubbed: {scrubber.scrub(test_text)}")
