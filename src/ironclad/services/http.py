from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import time
import requests


@dataclass(slots=True)
class HttpConfig:
    default_ttl_s: int = 60
    timeout: float = 10.0
    cache_enabled: bool = True


class HTTPClient:
    def __init__(self, config: HttpConfig | None = None):
        self.config = config or HttpConfig()
        self._cache: dict[tuple[Any, ...], tuple[float, Any]] = {}

    def _cache_key(
        self,
        url: str,
        params: Mapping[str, Any] | None,
        headers: Mapping[str, Any] | None,
    ) -> tuple[Any, ...]:
        key_params = tuple(sorted((params or {}).items()))
        key_headers = tuple(sorted((headers or {}).items()))
        return (url, key_params, key_headers)

    def get_json(
        self,
        url: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, Any] | None = None,
        ttl_s: int | None = None,
    ) -> Any:
        ttl = ttl_s if ttl_s is not None else self.config.default_ttl_s
        cache_enabled = self.config.cache_enabled and ttl > 0
        key = self._cache_key(url, params, headers)
        now = time.time()
        if cache_enabled and key in self._cache:
            expires_at, cached = self._cache[key]
            if now < expires_at:
                return cached

        response = requests.get(url, params=params, headers=headers, timeout=self.config.timeout)
        response.raise_for_status()
        data = response.json()

        if cache_enabled:
            self._cache[key] = (now + ttl, data)
        return data
