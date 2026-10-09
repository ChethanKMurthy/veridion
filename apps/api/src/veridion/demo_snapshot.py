"""Export the demo workspace as static files for the public, no-login demo.

The snapshot is a recording of real API responses (GET requests made through the
application itself), so the public demo shows exactly what the product shows,
without running a server or spending model credits per visitor.

Layout:
    <out>/manifest.json                       entry points and generation metadata
    <out>/api/<path>[@k=v].json               one file per recorded GET request
    <out>/pages/<document id>/<n>.png         rendered document pages
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

from veridion.config import configure, get_settings

SCALE = 1.5


def path_to_file(root: Path, path: str, params: dict | None = None) -> Path:
    clean = path.strip("/")
    suffix = ""
    if params:
        suffix = "@" + urlencode(sorted(params.items())).replace("&", "@")
    return root / "api" / f"{clean}{suffix}.json"


def export_snapshot(out: Path, email: str, password: str) -> dict:
    configure(**{**_current_overrides(), "embedded_worker": False, "rate_limit_enabled": False})
    from fastapi.testclient import TestClient

    from veridion.main import create_app

    app = create_app()
    if out.exists():
        shutil.rmtree(out)
    (out / "api").mkdir(parents=True)
    recorded: list[str] = []
    images = 0

    with TestClient(app) as client:
        r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        if r.status_code != 200:
            raise SystemExit(f"Demo login failed ({r.status_code}): {r.text}. Run `veridion seed demo` first.")

        def get(path: str, params: dict | None = None):
            response = client.get(f"/api/v1{path}", params=params)
            if response.status_code != 200:
                raise SystemExit(f"GET {path} failed: {response.status_code} {response.text[:300]}")
            data = response.json()
            target = path_to_file(out, path, params)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(data, separators=(",", ":")))
            recorded.append(path + (f"?{urlencode(params)}" if params else ""))
            return data

        me = get("/auth/me")
        get("/org")
        get("/dashboard")
        sets = get("/requirement-sets")
        for rs in sets:
            get(f"/requirement-sets/{rs['id']}")
        companies = get("/companies")
        focal_id = None
        for c in companies:
            cid = c["id"]
            detail = get(f"/companies/{cid}")
            if detail.get("peer_ids"):
                focal_id = focal_id or cid
            get(f"/companies/{cid}/overview")
            docs = get(f"/companies/{cid}/documents")
            get(f"/companies/{cid}/documents", {"include_superseded": "true"})
            get(f"/companies/{cid}/metrics")
            get(f"/companies/{cid}/benchmark", {"period": "FY2025"})
            get(f"/companies/{cid}/actions")
            get(f"/companies/{cid}/actions", {"status": "open"})
            for key in {rs["key"] for rs in sets}:
                get(f"/companies/{cid}/applicability", {"set_key": key})
            runs = get(f"/companies/{cid}/runs")
            for doc in docs:
                get(f"/documents/{doc['id']}")
                get(f"/documents/{doc['id']}/passages")
                for page in range(1, (doc.get("page_count") or 0) + 1):
                    response = client.get(f"/api/v1/documents/{doc['id']}/pages/{page}/image",
                                          params={"scale": SCALE})
                    target = out / "pages" / doc["id"] / f"{page}.png"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(response.content)
                    images += 1
            for run in runs:
                if run["status"] != "completed":
                    continue
                rid = run["id"]
                get(f"/runs/{rid}")
                for fmt in ("json", "csv", "md"):
                    exported = client.get(f"/api/v1/runs/{rid}/export", params={"format": fmt})
                    target = out / "exports" / f"{rid}.{fmt}"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(exported.content)
                findings = get(f"/runs/{rid}/findings")
                get(f"/runs/{rid}/report")
                if run.get("previous_run_id"):
                    get(f"/runs/{rid}/diff")
                passage_ids: set[str] = set()
                for f in findings:
                    trail = get(f"/findings/{f['id']}")
                    passage_ids.update(trail.get("passages", {}).keys())
                for pid in sorted(passage_ids):
                    target = path_to_file(out, f"/passages/{pid}")
                    if not target.exists():
                        get(f"/passages/{pid}")

    _write_highlights(out, focal_id)

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "organization": me["organization"]["name"],
        "focal_company_id": focal_id,
        "company_ids": [c["id"] for c in companies],
        "page_scale": SCALE,
        "llm_model": next((r.get("llm_model") for r in _all_runs(out) if r.get("llm_model")), None),
        "notice": "Fictional sample companies and documents. Results were produced by the Veridion engine "
                  "and recorded for this read-only demonstration.",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    return {"responses": len(recorded), "page_images": images, "bytes": size, "out": str(out)}


def _all_runs(out: Path) -> list[dict]:
    runs = []
    for f in (out / "api" / "runs").glob("*.json"):
        try:
            runs.append(json.loads(f.read_text()))
        except (ValueError, OSError):
            continue
    return runs


def _current_overrides() -> dict:
    s = get_settings()
    return {k: getattr(s, k) for k in ("database_url", "storage_dir", "llm_provider", "llm_model", "groq_api_key",
                                       "llm_base_url", "llm_api_key", "veridion_env", "secret_key")}


def _load(out: Path, path: str, params: dict | None = None):
    target = path_to_file(out, path, params)
    return json.loads(target.read_text()) if target.exists() else None


def _write_highlights(out: Path, focal_id: str | None) -> None:
    """A compact digest of the demo for the marketing site (imported at build time)."""
    if not focal_id:
        return
    company = _load(out, f"/companies/{focal_id}")
    runs = [r for r in (_load(out, f"/companies/{focal_id}/runs") or []) if r["status"] == "completed"]
    if not company or not runs:
        return
    latest = runs[0]
    findings = _load(out, f"/runs/{latest['id']}/findings") or []
    conflict = next((f for f in findings if f["status"] == "conflicting"), None)
    trail = _load(out, f"/findings/{conflict['id']}") if conflict else None

    def crop(passage: dict) -> dict:
        doc = passage.get("document") or {}
        sizes = doc.get("page_sizes") or []
        return {
            "src": f"/demo/pages/{passage['document_id']}/{passage['page']}.png",
            "size": sizes[passage["page"] - 1] if len(sizes) >= passage["page"] else [595, 842],
            "bbox": passage["bbox"], "document": doc.get("short_name"), "title": doc.get("title"),
            "page": passage["page"], "text": passage["text"], "id": passage["id"],
        }

    conflict_view = None
    if trail and trail["finding"]["conflicts"]:
        c = trail["finding"]["conflicts"][0]
        passages = trail["passages"]
        conflict_view = {
            "finding_id": conflict["id"],
            "display_code": trail["requirement"]["display_code"],
            "title": trail["requirement"]["title"],
            "rationale": trail["finding"]["rationale"],
            "conflict": c,
            "low": crop(passages[c["low"]["passage_id"]]) if c["low"]["passage_id"] in passages else None,
            "high": crop(passages[c["high"]["passage_id"]]) if c["high"]["passage_id"] in passages else None,
            "action": (trail["actions"] or [None])[0],
        }
    bench = _load(out, f"/companies/{focal_id}/benchmark", {"period": "FY2025"}) or {}
    rows = {r["metric_key"]: r for r in bench.get("rows", [])}
    diff = _load(out, f"/runs/{latest['id']}/diff")
    overview = _load(out, f"/companies/{focal_id}/overview") or {}
    highlights = {
        "key_disclosures": overview.get("key_disclosures", [])[:8],
        "company": {k: company.get(k) for k in ("id", "name", "industry", "country", "fiscal_year_end")},
        "run": {k: latest.get(k) for k in ("id", "requirement_set_id", "mode", "llm_model", "period_label", "summary",
                                           "finished_at")},
        "findings": [{k: f.get(k) for k in ("id", "display_code", "title", "status", "completeness", "missing_elements",
                                            "primary_evidence", "evidence_count", "method")} for f in findings],
        "conflict": conflict_view,
        "benchmark": {
            "companies": bench.get("companies", []),
            "rows": [rows[k] for k in ("ghg_scope1", "energy_total", "ghg_scope3") if k in rows],
        },
        "diff": diff,
    }
    target = out.parent.parent / "src" / "content" / "demo-highlights.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(highlights, indent=1))
