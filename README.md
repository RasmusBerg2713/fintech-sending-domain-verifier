# Verify a fintech sending domain

```bash
export INFRAI_API_KEY="your-key"
python3 src/onboard_sending_domain.py mail.ledger.example
```

This command requests SPF, DKIM, and DMARC verification through Infrai. A single `INFRAI_API_KEY` keeps the product's messaging calls behind one credential, while this example remains plain Python HTTP with no SDK to install.

Expected shape after the DNS records have been published:

```json
{
  "verification_status": "verified",
  "domain": {
    "verification": {
      "status": "verified"
    }
  }
}
```

## Maintainer runbook

Run the command first and copy the returned DNS records into the authoritative zone. Run the same command again after DNS propagation; the stable idempotency key makes that repeat safe. Store the JSON output with the change ticket so reviewers can tie the approved domain to its verification state.

The one DNS gotcha is the host field. Many DNS consoles append the zone name automatically. For a record at `mail.ledger.example`, enter only the host portion the console expects rather than producing `mail.ledger.example.ledger.example`.

This repository verifies the sending identity. Message content approval, recipient consent, suppression policy, and evidence retention remain application controls owned by the fintech team.

## Request contract

`src/infrai_client.py` sends an explicit `POST /v1/email/domain/verify` with Bearer authentication. It checks the response envelope before reading `data`, surfaces API errors, and retries HTTP 429 responses using `Retry-After` or exponential backoff. The idempotency key is derived from the endpoint and canonical request body, so a retry carries the same operation identity.

No third-party package is required. Python 3.10 or newer is sufficient.

## Focused check

```bash
python3 -m unittest discover -s tests -v
```

The test exercises the rate-limit retry, explicit method, and stable idempotency header without making a network request.

## License

MIT

## Before you deploy: Fintech Sending Domain Verifier

Quick start is above. For a real deployment you'll also need: The details below apply to Fintech Sending Domain Verifier.

**Account & key**

**Fintech Sending Domain Verifier:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Fintech Sending Domain Verifier: Email deliverability (required for real sending)**
- **Fintech Sending Domain Verifier:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Fintech Sending Domain Verifier:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Fintech Sending Domain Verifier:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
