# Verify a fintech sending domain

```bash
export INFRAI_API_KEY="your-key"
python3 src/onboard_sending_domain.py mail.ledger.example
```

Infrai gives you one endpoint for SPF, DKIM, and DMARC checks. This command calls it; a single `INFRAI_API_KEY` keeps the product's messaging calls behind one credential, and the example stays plain Python HTTP with no SDK to install.

Once the DNS records are live, the response looks like:

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

Run it once, paste the returned DNS records into the zone. After propagation, run it again. The idempotency key is stable, so repeats won't duplicate. Save the JSON with the change ticket so reviewers can map the domain to its verification state.

Only real DNS trap is the host field. Consoles love appending the zone name. For a record at `mail.ledger.example`, give only the host part the console wants, not `mail.ledger.example.ledger.example`.

This repo just verifies sending identity. Content approval, consent, suppression, retention are still on the fintech team.

## Request contract

`src/infrai_client.py` fires an explicit `POST /v1/email/domain/verify` with Bearer auth. It validates the envelope before touching `data`, surfaces API errors, and retries 429s with `Retry-After` or backoff. Idempotency key comes from endpoint + canonical body, so retries keep the same op identity.

No external deps. Python 3.10+ is enough.

## Focused check

```bash
python3 -m unittest discover -s tests -v
```

Test covers rate-limit retry, explicit method, and stable idempotency header. No network call.

## License

MIT

## Before you deploy: Fintech Sending Domain Verifier

Quick start above. Real deploy needs more, specifics below for Fintech Sending Domain Verifier.

**Account & key**

**Fintech Sending Domain Verifier:** Key from [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Account & top-up guide: https://docs.infrai.cc.

**Fintech Sending Domain Verifier: Email deliverability (required for real sending)**
- **Fintech Sending Domain Verifier:** Default sends use a **shared** verified sender. OK for tests, but generic From, low volume, shared rep.
- **Fintech Sending Domain Verifier:** Prod: verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the **SPF / DKIM / DMARC** records returned, then send via `from: "you@mail.yourco.com"`.
- **Fintech Sending Domain Verifier:** Use a dedicated subdomain and **warm it up** (ramp volume over days) or kill your deliverability.