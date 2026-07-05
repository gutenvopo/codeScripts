from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SearchResult:
    name: str
    size: int
    seeders: int
    leechers: int
    site_url: str
    description_url: str
    file_url: str
    engine: str

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> SearchResult:
        return cls(
            name=str(data.get("fileName") or ""),
            size=_to_int(data.get("fileSize"), -1),
            seeders=_to_int(data.get("nbSeeders"), 0),
            leechers=_to_int(data.get("nbLeechers"), 0),
            site_url=str(data.get("siteUrl") or ""),
            description_url=str(data.get("descrLink") or ""),
            file_url=str(data.get("fileUrl") or ""),
            engine=str(data.get("engineName") or ""),
        )

    @property
    def copy_url(self) -> str:
        return self.file_url or self.description_url or self.site_url


def sort_results(
    results: list[SearchResult], key: str, reverse: bool = False
) -> list[SearchResult]:
    key_map = {
        "name": lambda item: item.name.lower(),
        "size": lambda item: item.size,
        "seeders": lambda item: item.seeders,
        "leechers": lambda item: item.leechers,
        "engine": lambda item: item.engine.lower(),
        "site_url": lambda item: item.site_url.lower(),
    }
    return sorted(results, key=key_map.get(key, key_map["name"]), reverse=reverse)


def filter_results(results: list[SearchResult], text: str) -> list[SearchResult]:
    needle = text.casefold().strip()
    if not needle:
        return list(results)
    return [
        item
        for item in results
        if needle in item.name.casefold() or needle in item.engine.casefold()
    ]


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
