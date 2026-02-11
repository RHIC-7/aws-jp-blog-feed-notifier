"""Extract main content text from AWS blog HTML pages.

This module is intentionally dependency-free (stdlib only) to keep Lambda
packaging simple.
"""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser


class _HTMLTextExtractor(HTMLParser):
    _BLOCK_TAGS = {
        "p",
        "br",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "div",
        "section",
        "article",
        "blockquote",
        "pre",
        "tr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "br":
            self._parts.append("\n")
        elif tag == "li":
            self._parts.append("\n- ")
        elif tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if data:
            self._parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._skip_depth:
            return
        self._parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._skip_depth:
            return
        self._parts.append(f"&#{name};")

    def text(self) -> str:
        raw = "".join(self._parts)
        raw = html.unescape(raw)
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        raw = re.sub(r"[ \t\f\v]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        lines = [ln.strip() for ln in raw.split("\n")]
        return "\n".join([ln for ln in lines if ln])


def _slice_tag_block(html_text: str, open_pat: str, tag_name: str) -> str:
    m = re.search(open_pat, html_text, flags=re.IGNORECASE)
    if not m:
        return ""

    start = m.start()
    depth = 0
    token_re = r"</?%s\b" % re.escape(tag_name)
    for t in re.finditer(token_re, html_text[start:], re.I):
        token = t.group(0).lower()
        if token.startswith("</"):
            depth -= 1
            if depth == 0:
                end = start + t.end()
                end_close = html_text.lower().find(f"</{tag_name}>", end)
                if end_close != -1:
                    return html_text[start:end_close + len(tag_name) + 3]
                break
        else:
            depth += 1
    return ""


def extract_aws_blog_main_content(page_html: str) -> str:
    """Extract main content text from an AWS blog post HTML.

    Prioritizes `property="articleBody"` section; falls back to an `<article>`
    with `blog-post` class.
    """

    section = _slice_tag_block(
        page_html,
        r"<section\b[^>]*\bproperty=\"articleBody\"[^>]*>",
        "section",
    )
    if not section:
        section = _slice_tag_block(
            page_html,
            r"<article\b[^>]*\bclass=\"[^\"]*\bblog-post\b[^\"]*\"[^>]*>",
            "article",
        )
    if not section:
        return ""

    parser = _HTMLTextExtractor()
    parser.feed(section)
    return parser.text()


def html_to_text(page_html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(page_html)
    return parser.text()


def extract_main_text(page_html: str) -> str:
    main = extract_aws_blog_main_content(page_html)
    if main:
        return main
    return html_to_text(page_html)
