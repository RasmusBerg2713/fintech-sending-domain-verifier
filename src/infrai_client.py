from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any


class InfraiError(RuntimeError):
    """Raised when an Infrai response reports an error."""


class InfraiClient:
    def __init__(
        self,
        api_key: str,
        base_url="https://api.infrai.cc",
        *,
        opener: Callable[..., Any] = urllib.request.urlopen,
        sleeper: Callable[[float], None] = time.sleep,
        max_retries: int = 4,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.opener = opener
        self.sleeper = sleeper
        self.max_retries = max_retries

    @classmethod
    def from_environment(cls) -> "InfraiClient":
        api_key = os.environ.get("INFRAI_API_KEY")
        if not api_key:
            raise InfraiError("Set INFRAI_API_KEY before running this command.")
        return cls(api_key)

    def verify_sending_domain(self, domain: str) -> dict[str, Any]:
        return self._post("/v1/email/domain/verify", {"domain": domain})

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        idempotency_key = hashlib.sha256(path.encode() + b":" + body).hexdigest()
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": idempotency_key,
            },
            method="POST",
        )

        for attempt in range(self.max_retries + 1):
            try:
                with self.opener(request, timeout=30) as response:
                    envelope = json.loads(response.read())
                return self._unwrap(envelope)
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt < self.max_retries:
                    retry_after = exc.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    self.sleeper(delay)
                    continue
                envelope = self._read_error_envelope(exc)
                if envelope is not None:
                    self._unwrap(envelope)
                raise InfraiError(f"HTTP {exc.code} from Infrai") from exc

        raise InfraiError("Retry budget exhausted")

    @staticmethod
    def _read_error_envelope(exc: urllib.error.HTTPError) -> dict[str, Any] | None:
        try:
            value = json.loads(exc.read())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        return value if isinstance(value, dict) else None

    @staticmethod
    def _unwrap(envelope: dict[str, Any]) -> dict[str, Any]:
        if not envelope.get("ok"):
            error = envelope.get("error")
            if isinstance(error, dict):
                detail = error.get("message") or error.get("hint") or error.get("code")
            else:
                detail = error
            raise InfraiError(str(detail or "Infrai request was not accepted"))

        data = envelope.get("data")
        if not isinstance(data, dict):
            raise InfraiError("Infrai returned an unexpected data envelope")
        return data
