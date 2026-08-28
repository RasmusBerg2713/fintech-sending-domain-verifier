import io
import json
import unittest
import urllib.error

from src.infrai_client import InfraiClient


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.body = json.dumps(payload).encode()

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class DomainVerificationTest(unittest.TestCase):
    def test_retries_429_with_same_idempotency_key(self) -> None:
        requests = []
        sleeps = []

        def opener(request, data=None, timeout=None):
            self.assertIsNone(data)
            self.assertEqual(timeout, 30)
            requests.append(request)
            if len(requests) == 1:
                raise urllib.error.HTTPError(
                    request.full_url,
                    429,
                    "rate limited",
                    {"Retry-After": "3"},
                    io.BytesIO(b""),
                )
            return FakeResponse(
                {"ok": True, "data": {"verification": {"status": "pending"}}}
            )

        client = InfraiClient("test-key", opener=opener, sleeper=sleeps.append)
        result = client.verify_sending_domain("mail.ledger.example")

        self.assertEqual(result["verification"]["status"], "pending")
        self.assertEqual(sleeps, [3.0])
        self.assertEqual(requests[0].method, "POST")
        self.assertEqual(
            requests[0].get_header("Idempotency-key"),
            requests[1].get_header("Idempotency-key"),
        )


if __name__ == "__main__":
    unittest.main()
