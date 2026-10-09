# Security

## Reporting a vulnerability

Please report suspected security issues through the website's contact form (`/contact?topic=security`, choose "Security report"), not through public issues. Describe the issue and how to reach you, but leave out exploit details until we reply with a secure channel. Do not access data that is not yours, degrade the service, or use social engineering, and give us reasonable time to fix an issue before disclosing it. There is no bug bounty at present.

## Controls

The controls that exist today are listed on the website's security page (`/trust/security`) and in [docs/architecture.md](docs/architecture.md#security-model). Deployment settings that affect security (`SECRET_KEY`, `COOKIE_SECURE`, `FORWARDED_ALLOW_IPS`, `ALLOW_REGISTRATION`) are covered in [docs/deployment.md](docs/deployment.md#production-checklist).

## Secrets in this repository

Never commit `.env` files or API keys; `.gitignore` excludes `.env`, `.env.*` (except `.env.example`) and runtime data under `var/`. If a key is exposed anywhere, rotate it with its provider rather than only deleting the file.
