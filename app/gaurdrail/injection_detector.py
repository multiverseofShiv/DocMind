from typing import List, Tuple
import re

_PATTERNS = [
    # Override attempts
    r"(?i)ignore (all|previous|above) instructions",
    r"(?i)disregard (all|previous|system) instructions",

    # Role hijacking
    r"(?i)you are now (a|an)? ?(admin|developer|system|root)",
    r"(?i)act as (a|an)? ?(admin|developer|unrestricted ai)",

    # Prompt leaking
    r"(?i)(show|reveal|display) (your )?(system prompt|instructions|rules)",

    # Jailbreak phrases
    r"(?i)jailbreak",
    r"(?i)do anything now",

    # Sensitive data requests
    r"(?i)(api key|password|secret|token|credentials)",

    # Instruction override claims
    r"(?i)this (overrides|replaces) (all|previous) instructions",

    # Output manipulation
    r"(?i)respond only with",
]


_RE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _PATTERNS]


def  detect_injection(text: str) -> Tuple[bool, float, List[str]]:
    if not text:
        return False, 0.0, []
    
    matches = []
    
    for rx in _RE_PATTERNS:
        if rx.search(text):
            matches.append(rx.pattern)
            
            
    is_inj = len(matches)>0
    score = min(1.0, 0.2*len(matches)) if is_inj else 0.0
    return is_inj, score, matches
        