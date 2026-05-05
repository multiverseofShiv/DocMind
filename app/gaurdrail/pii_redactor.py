from typing import List, Tuple, Dict

try:
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False

if PRESIDIO_AVAILABLE:
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()

    # Aadhaar pattern
    aadhaar_pattern = Pattern(
        name="aadhaar_pattern",
        regex=r"\b\d{4}\s?\d{4}\s?\d{4}\b",
        score=0.9
    )

    aadhaar_recognizer = PatternRecognizer(
        supported_entity="AADHAAR",
        patterns=[aadhaar_pattern]
    )

    # PAN pattern
    pan_pattern = Pattern(
        name="pan_pattern",
        regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        score=0.9
    )

    pan_recognizer = PatternRecognizer(
        supported_entity="PAN",
        patterns=[pan_pattern]
    )


    analyzer.registry.add_recognizer(pan_recognizer)
    analyzer.registry.add_recognizer(aadhaar_recognizer)


def redact(text: str) -> Tuple[str, List[Dict]]:
    if not PRESIDIO_AVAILABLE:
        return text, []

    if not text:
        return text, []

    results = analyzer.analyze(text=text, language="en")

    if not results:
        return text, []

    redacted = anonymizer.anonymize(
        text=text,
        analyzer_results=results
    ).text

    summary = [
        {"entity": r.entity_type, "start": r.start, "end": r.end}
        for r in results
    ]

    return redacted, summary