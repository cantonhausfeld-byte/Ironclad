from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping

import requests


@dataclass
class HttpConfig:
    default_ttl_s: int = 0


class HTTPClient:
    def __init__(self, config: HttpConfig | None = None):
        self.config = config or HttpConfig()
        self._cache: dict[tuple[Any, ...], tuple[float, Any]] = {}

    def get_json(self, url: str, *, params: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None) -> Any:
        key = self._cache_key(url, params=params, headers=headers)
        ttl = self.config.default_ttl_s
        if ttl > 0:
            cached = self._cache.get(key)
            if cached:
                ts, payload = cached
                if (time.monotonic() - ts) < ttl:
                    return payload

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        payload = response.json()

        if ttl > 0:
            self._cache[key] = (time.monotonic(), payload)
        return payload

    def _cache_key(self, url: str, *, params: Mapping[str, Any] | None, headers: Mapping[str, str] | None) -> tuple[Any, ...]:
        params_items = tuple(sorted((params or {}).items()))
        headers_items = tuple(sorted((headers or {}).items())) if headers else ()
        return (url, params_items, headers_items)
