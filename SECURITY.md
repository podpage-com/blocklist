# Security policy

Blocklist is security-adjacent infrastructure. Please do not publish credentials, exploitable deployment details, or active abuse data in public GitHub issues.

For vulnerabilities, contact the repository maintainers privately through the Podpage organization.

API keys are bearer credentials. Deployments should use HTTPS, restrict Django Admin appropriately, rotate exposed keys immediately, and keep `SECRET_KEY` outside source control.

The project intentionally does not execute blocking actions against participant infrastructure.
