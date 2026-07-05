from __future__ import annotations

from qbsearch.core.result_model import SearchResult, filter_results, sort_results


def test_from_api_normalizes_missing_values() -> None:
    result = SearchResult.from_api({"fileName": "Test", "fileSize": "-1"})
    assert result.name == "Test"
    assert result.size == -1
    assert result.seeders == 0


def test_sort_results_by_seeders_descending() -> None:
    rows = [
        SearchResult("b", 20, 3, 0, "", "", "", "B"),
        SearchResult("a", 10, 8, 0, "", "", "", "A"),
    ]
    assert sort_results(rows, "seeders", reverse=True)[0].seeders == 8


def test_filter_results_checks_name_and_engine() -> None:
    rows = [SearchResult("Ubuntu", 1, 1, 1, "", "", "", "LimeTorrents")]
    assert filter_results(rows, "lime")
