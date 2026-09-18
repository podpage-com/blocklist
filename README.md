# Blocklist

Open-source shared infrastructure for exchanging IP abuse observations between independent organizations.

Blocklist is deliberately not an enforcement service. It does not manage Cloudflare, firewalls, WAFs, or blocking policy. Participants publish observations and independently decide how to use them.

## Quick start
```bash
cp .env.example .env
docker compose up --build
docker compose exec web python manage.py createsuperuser
```
Open http://localhost:8000/ for technical docs and /admin/ for administration.

## API
- POST /api/v1/observations/ — report/update an IP
- PUT /api/v1/observations/sync/ — authoritative sync of your current list
- GET /api/v1/observations/ — active network observations
- GET /api/v1/ips/<ip>/ — aggregated IP detail
- GET /api/v1/changes/?since=<ISO8601> — incremental feed
- GET /health/ — health check

Authenticate with `Authorization: Api-Key YOUR_KEY`.

## Principles
1. Information exchange, not centralized enforcement.
2. Every observation retains its source.
3. Consumers choose their own policies.
4. Observations expire.
5. API credentials are hashed at rest.
6. Keep integrations simple.

## License
MIT.
