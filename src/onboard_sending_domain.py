from __future__ import annotations

import argparse
import json

from infrai_client import InfraiClient, InfraiError


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Request SPF, DKIM, and DMARC verification for a sending domain."
    )
    parser.add_argument("domain", help="Domain used for regulated product email")
    args = parser.parse_args()

    try:
        data = InfraiClient.from_environment().verify_sending_domain(args.domain)
        status = data["verification"]["status"]
    except (InfraiError, KeyError, TypeError) as exc:
        parser.exit(1, f"domain verification failed: {exc}\n")

    print(json.dumps({"verification_status": status, "domain": data}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
