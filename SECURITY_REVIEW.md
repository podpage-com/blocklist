# Security review

Reviewed 2026-09-18.

## Fixed in this pass
- Production now refuses to boot without an explicit SECRET_KEY.
- Production security headers, HTTPS redirect, secure cookies, and HSTS enabled.
- Django password validators restored for admin accounts.
- Client cannot set Observation.active directly.
- Sync deactivation now updates updated_at so consumers see removals in the change feed.
- IP detail validates addresses instead of allowing malformed database lookups.
- Change-feed timestamps must be timezone-aware.
- Sync batch size and metadata payload size are bounded.
- Duplicate IPs in an authoritative sync are rejected.
- Production database connections require TLS when DATABASE_URL is configured.
- Render runs migrations as a pre-deploy step.

## Remaining design considerations before broad production use
1. API throttling uses Django's cache. Configure a shared cache (Redis) if the service runs multiple instances; database/API-key quotas are preferable for stronger abuse controls.
2. The change feed is capped at 5,000 rows but has no cursor. Add cursor-based pagination before volume approaches that size or consumers can miss changes.
3. Organization identity is visible to every authenticated participant. Confirm that this is intended; otherwise expose stable pseudonymous reporter IDs.
4. Metadata is shared verbatim with all participants. Establish a rule that metadata must never contain credentials, personal data, request bodies, or other secrets.
5. The authoritative sync endpoint intentionally deactivates everything omitted. Consumers should use retries/idempotency and should not call it with a partial list.
6. Admin should be protected operationally (strong password, ideally SSO/VPN/access proxy) even though it is not part of the participant API.
7. Consider an append-only audit/event table if historical accountability becomes important. The current row model preserves current state, not every mutation.
8. Dependency scanning and static analysis should be added to CI.

## Threat model
Blocklist assumes authenticated participants can submit incorrect or malicious observations. A report is therefore an assertion by a source, not truth. Consumers must retain local enforcement policy and should use reporter count/trust/allowlists as appropriate.
