import re
from typing import Tuple

# Patterns frequently used in prompt injection / role hijacking attacks
INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"(?i)disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"(?i)system\s*:\s*you\s+are",
    r"(?i)<\|im_start\|>",
    r"(?i)<\|im_end\|>",
    r"(?i)\[INST\]",
    r"(?i)\[/INST\]",
    r"(?i)you\s+must\s+act\s+as",
    r"(?i)bypass\s+all\s+restrictions",
    r"(?i)reveal\s+your\s+(initial|system)\s+prompt",
]

def sanitize_scraped_text(raw_text: str) -> Tuple[str, bool]:
    """
    Sanitizes crawled website content to protect the RAG pipeline against indirect prompt injection.
    Returns:
        (sanitized_text, was_injection_detected)
    """
    if not raw_text:
        return "", False

    # 1. Remove zero-width and control characters
    text = re.sub(r"[\u200B-\u200D\uFEFF\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", raw_text)

    # 2. Check for adversarial prompt injection patterns
    injection_detected = False
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            injection_detected = True
            # Neutralize the match by replacing with sanitized disclaimer
            text = re.sub(pattern, "[FILTERED_SUSPICIOUS_PAYLOAD]", text)

    # 3. Normalize multiple whitespaces and consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip(), injection_detected

def format_context_safely(chunks: list[dict]) -> str:
    """
    Formats retrieved chunks into an isolated XML structure (<vvce_context>)
    ensuring that retrieved content is clearly marked as external reference data.
    """
    context_parts = []
    for i, c in enumerate(chunks, 1):
        title = c.get("title", "VVCE Web Page")
        url = c.get("url", "https://vvce.ac.in")
        text = c.get("text", "")
        # Sanitize chunk text before wrapping
        clean_text, _ = sanitize_scraped_text(text)
        context_parts.append(
            f'<source_doc index="{i}" title="{title}" url="{url}">\n{clean_text}\n</source_doc>'
        )

    return "<vvce_context>\n" + "\n\n".join(context_parts) + "\n</vvce_context>"
