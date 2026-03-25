from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

def mask_pii(text: str) -> str:
    """Mask PII (Personal Identifiable Information) in a text using Microsoft Presidio."""
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    
    # Define the entities to detect (Phone, Address, Email, Name)
    results = analyzer.analyze(text=text, entities=["PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION", "PERSON"], language='en')
    
    # Apply masking
    anonymized_result = anonymizer.anonymize(
        text=text,
        analyzer_results=results
    )
    
    return anonymized_result.text
