# Veridion web

The Next.js application: marketing site, public demo (`/demo`) and the authenticated workspace (`/app`). See the [repository README](../../README.md) for the product.

## Develop

```bash
npm ci
npm run dev          # http://localhost:3000; proxies /api/* to VERIDION_API_URL (default http://127.0.0.1:8000)
npm run lint
npm run typecheck
npm run build
```

Run the API alongside it (`make dev` from the repository root starts both).

## How it is organised

| Path | Contents |
|---|---|
| `src/app/(site)/` | Marketing, trust, legal and research pages (static) |
| `src/app/(auth)/` | Sign-in and sign-up |
| `src/app/app/` | Live workspace; `src/proxy.ts` redirects visitors without a session |
| `src/app/demo/` | The same workspace screens on recorded data |
| `src/components/app/` | Workspace screens, the Evidence Explorer and the evidence trail inspector |
| `src/components/site/` | Site sections and illustrations |
| `src/components/ui/` | Shared primitives: buttons, fields, dialogs, status glyphs, meters |
| `src/lib/api/` | `DataClient` with `HttpClient` (live) and `SnapshotClient` (demo) implementations |
| `public/demo/` | Recorded API responses and page images (`veridion demo snapshot` regenerates them) |

Design tokens live in `src/app/globals.css` (`@theme`); the design system is described in [DESIGN.md](../../DESIGN.md).

## Notes

- The browser only ever calls this origin. `/api/*` is rewritten to the API in `next.config.ts`, so session cookies are first-party. Rewrites are compiled at build time: production builds need `VERIDION_API_URL` set to the API's address.
- `output: "standalone"` produces the self-contained server used by the `Dockerfile`.
- The demo is read-only: actions that would change data explain that they need a workspace.
