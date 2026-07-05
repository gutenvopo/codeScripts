from __future__ import annotations

import re

import pytest

from qbsearch.core.regex_filter import compile_pattern, longest_alphanumeric_token, regex_matches


def test_longest_alphanumeric_token_extracts_broad_query() -> None:
    assert longest_alphanumeric_token(r"^Ubuntu.*(Server|Desktop).*24\.04$") == "Desktop"


def test_regex_matches_is_case_insensitive() -> None:
    pattern = compile_pattern("ubuntu.*iso")
    assert regex_matches(pattern, "Ubuntu Desktop ISO")


def test_compile_pattern_raises_re_error() -> None:
    with pytest.raises(re.error):
        compile_pattern("[")
