from __future__ import annotations

import re


def compile_pattern(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE)


def longest_alphanumeric_token(pattern: str) -> str:
    cleaned = re.sub(r"\\[AbBdDsSwWZz]", " ", pattern)
    cleaned = re.sub(r"\[[^\]]*\]", " ", cleaned)
    cleaned = re.sub(r"\(\?[:=!<].*?\)", " ", cleaned)
    cleaned = re.sub(r"[\\^$.*+?{}()|]", " ", cleaned)
    tokens = re.findall(r"[A-Za-z0-9]{2,}", cleaned)
    if not tokens:
        return pattern.strip()
    return max(tokens, key=len)


def regex_matches(pattern: re.Pattern[str] | None, value: str) -> bool:
    return pattern.search(value) is not None if pattern else True
