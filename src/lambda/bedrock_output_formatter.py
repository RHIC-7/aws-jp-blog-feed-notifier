"""Format/normalize text returned by Bedrock (Nova) for chat posting."""

from __future__ import annotations

import re

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
_QUOTE_PUNCT_RE = re.compile(r'(?:\\")|(?:")')


def _cleanup_quote_artifacts(text: str) -> str:
    """Remove obviously spurious quote artifacts from model output.

    The prompt does not require quoting, but Nova output can include stray
    `"` or `"。`-like fragments. We keep this conservative to avoid removing
    meaningful quotes inside the sentence.
    """

    s = text.strip()

    # Drop wrapping quotes when the whole field is quoted.
    if (s.startswith('"') and s.endswith('"')) and len(s) >= 2:
        s = s[1:-1].strip()
    if (s.startswith('\\"') and s.endswith('\\"')) and len(s) >= 4:
        s = s[2:-2].strip()

    # Remove quote tokens right before punctuation / end-of-line.
    s = re.sub(r'(?:\\")(?=[、。．，,\.!\?])', "", s)
    s = re.sub(r'"(?=[、。．，,\.!\?])', "", s)
    s = re.sub(r'(?:\\")\s*$', "", s)
    s = re.sub(r'"\s*$', "", s)
    s = re.sub(r'^\s*(?:\\")', "", s)
    s = re.sub(r'^\s*"', "", s)

    return s


def bedrock_output_to_text(response: dict) -> str:
    content = (
        (((response or {}).get("output") or {}).get("message") or {}).get(
            "content",
            [],
        )
        or []
    )
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            parts.append(block["text"])
    return "\n".join(parts).strip()


def _extract_tag(text: str, tag: str) -> str:
    m = re.search(
        rf"<{re.escape(tag)}>(.*?)</{re.escape(tag)}>",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return (m.group(1).strip() if m else "")


def _normalize_text(text: str) -> str:
    text = _CONTROL_CHARS_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def format_nova_summary(raw_text: str) -> str:
    """Extract/format `<thinking>` and `<summary>` blocks when present.

    Returns a clean, plain-text string safe to embed in JSON.
    """

    raw_text = _normalize_text(raw_text)

    thinking = _extract_tag(raw_text, "thinking")
    summary = _extract_tag(raw_text, "summary")

    if thinking:
        lines = [ln.strip() for ln in thinking.split("\n") if ln.strip()]
        bullet_lines: list[str] = []
        for ln in lines:
            ln = _cleanup_quote_artifacts(ln)
            if ln.startswith("-"):
                if not ln.startswith("- "):
                    ln = "- " + ln[1:].lstrip()
                bullet_lines.append(ln)
            else:
                ln = ln.lstrip("•").strip()
                bullet_lines.append(f"- {ln}")
        thinking = "\n".join(bullet_lines)

    if summary:
        summary = " ".join(
            [p.strip() for p in summary.splitlines() if p.strip()],
        )
        summary = _cleanup_quote_artifacts(summary)

    if thinking and summary:
        return f"{thinking}\n\n{summary}"
    if summary:
        return summary
    if thinking:
        return thinking

    raw_text = re.sub(r"</?(thinking|summary)>", "", raw_text, flags=re.I)
    return raw_text.strip()
