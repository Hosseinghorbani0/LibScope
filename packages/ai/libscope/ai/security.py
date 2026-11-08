"""
AI Security Controls and Prompt Injection Defenses.
Sanitizes external package metadata, issues, and documentation before sending to LLM.
"""
import re
from typing import Optional


# Patterns often used in prompt injection attempts in READMEs or package descriptions
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_end\|>", re.IGNORECASE),
    re.compile(r"\[SYSTEM_PROMPT\]", re.IGNORECASE),
]


def sanitize_untrusted_text(raw_text: Optional[str], max_length: int = 3000) -> str:
    """
    Sanitize untrusted text (such as READMEs, descriptions, keywords, user comments):
    1. Truncate to maximum bounded length.
    2. Redact suspicious prompt injection triggers.
    3. Neutralize XML-like tag injections.
    4. Wrap in strict untrusted data boundaries.
    """
    if not raw_text:
        return "[Empty or None]"

    cleaned = str(raw_text).strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "... [TRUNCATED FOR SIZE]"

    # Replace known prompt injection triggers with safe warning tags
    for pat in INJECTION_PATTERNS:
        cleaned = pat.sub("[REDACTED_UNTRUSTED_PATTERN]", cleaned)

    # Neutralize closing untrusted_content tags
    cleaned = cleaned.replace("</untrusted_external_content>", "&lt;/untrusted_external_content&gt;")

    return f"<untrusted_external_content>\n{cleaned}\n</untrusted_external_content>"

