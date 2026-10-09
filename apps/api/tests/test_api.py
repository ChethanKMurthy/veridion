"""HTTP API: authentication, tenancy, workflow, exports and plan limits."""

from __future__ import annotations

from veridion.jobs import run_pending

from .conftest import SAMPLES, register


def _upload(client, company_id, slug, doc_type="sustainability_report", period="FY2025"):
    with open(SAMPLES / f"{slug}.pdf", "rb") as fh:
        r = client.post(f"/api/v1/companies/{company_id}/documents",
                        files={"file": (f"{slug}.pdf", fh, "application/pdf")},
                        data={"doc_type": doc_type, "period_label": period})
    assert r.status_code == 201, r.text
    return r.json()


def _company(client, name="Aldermere Materials Group", fye="12-31"):
    r = client.post("/api/v1/companies", json={"name": name, "industry": "Building materials", "fiscal_year_end": fye})
    assert r.status_code == 201, r.text
    return r.json()


def test_health(client):
    assert client.get("/api/v1/health").json()["status"] == "ok"


def test_register_login_logout(client):
    me = register(client)
    assert me["role"] == "owner" and me["organization"]["plan"] == "explorer"
    assert client.get("/api/v1/auth/me").status_code == 200
    client.post("/api/v1/auth/logout")
    client.cookies.clear()
    assert client.get("/api/v1/auth/me").status_code == 401
    bad = client.post("/api/v1/auth/login", json={"email": "analyst@example.com", "password": "wrong-password"})
    assert bad.status_code == 401
    ok = client.post("/api/v1/auth/login", json={"email": "analyst@example.com", "password": "a-long-password"})
    assert ok.status_code == 200
    assert register_conflict(client).status_code == 409


def test_login_limits_ignore_forwarded_headers_and_cap_each_account(client, monkeypatch):
    from fastapi.testclient import TestClient

    from veridion.config import get_settings

    register(client)
    client.cookies.clear()
    monkeypatch.setattr(get_settings(), "rate_limit_enabled", True)
    wrong = {"email": "analyst@example.com", "password": "wrong-password"}

    # Sending a different X-Forwarded-For on every attempt does not reset the per-address limit.
    codes = [client.post("/api/v1/auth/login", json=wrong, headers={"X-Forwarded-For": f"203.0.113.{i}"}).status_code
             for i in range(11)]
    assert codes == [401] * 10 + [429]

    # Guesses spread across many real addresses still stop at the per-account ceiling (30 per 15 minutes).
    codes = []
    for i in range(25):
        other = TestClient(client.app, client=(f"198.51.100.{i}", 50000), headers={"X-Veridion-Client": "web"})
        codes.append(other.post("/api/v1/auth/login", json=wrong).status_code)
    assert codes == [401] * 20 + [429] * 5


def test_registration_can_be_closed_for_an_invite_only_pilot(client, monkeypatch):
    from veridion.config import get_settings

    monkeypatch.setattr(get_settings(), "allow_registration", False)
    r = client.post("/api/v1/auth/register", json={"name": "x", "email": "new@example.com", "password": "a-long-password",
                                                   "organization": "New Co"})
    assert r.status_code == 403 and r.json()["code"] == "registration_closed"


def register_conflict(client):
    return client.post("/api/v1/auth/register", json={"name": "x", "email": "analyst@example.com",
                                                      "password": "a-long-password", "organization": "Other"})


def test_weak_password_rejected(client):
    r = client.post("/api/v1/auth/register", json={"name": "x", "email": "x@example.com", "password": "short",
                                                   "organization": "Org"})
    assert r.status_code == 422


def test_cookie_requests_need_the_client_header(client):
    register(client)
    del client.headers["X-Veridion-Client"]
    r = client.post("/api/v1/companies", json={"name": "No header"})
    assert r.status_code == 403
    client.headers["X-Veridion-Client"] = "web"
    assert client.post("/api/v1/companies", json={"name": "With header"}).status_code == 201


def test_bearer_tokens_work_without_csrf_header(client):
    register(client)
    token = client.cookies.get("veridion_session")
    client.cookies.clear()
    del client.headers["X-Veridion-Client"]
    r = client.post("/api/v1/companies", json={"name": "API client"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 201


def test_tenants_cannot_see_each_other(client):
    register(client, email="a@example.com", org="Org A")
    company = _company(client)
    token_a = client.cookies.get("veridion_session")
    client.cookies.clear()
    register(client, email="b@example.com", org="Org B")
    assert client.get(f"/api/v1/companies/{company['id']}").status_code == 404
    assert client.get("/api/v1/companies").json() == []
    assert client.patch(f"/api/v1/companies/{company['id']}", json={"name": "hijack"}).status_code == 404
    client.cookies.clear()
    r = client.get(f"/api/v1/companies/{company['id']}", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code == 200


def test_upload_validation(client):
    register(client)
    company = _company(client)
    r = client.post(f"/api/v1/companies/{company['id']}/documents",
                    files={"file": ("notes.txt", b"hello", "text/plain")}, data={"doc_type": "other"})
    assert r.status_code == 400 and "PDF" in r.json()["detail"]
    r = client.post(f"/api/v1/companies/{company['id']}/runs", json={"requirement_set_id": "gri-302-305-2016@1.1.0"})
    assert r.status_code == 400 and "Upload" in r.json()["detail"]


def test_same_file_twice_is_rejected(client):
    register(client)
    first = _company(client)
    doc = _upload(client, first["id"], "corvane-sustainability-update-2025")
    with open(SAMPLES / "corvane-sustainability-update-2025.pdf", "rb") as fh:
        r = client.post(f"/api/v1/companies/{first['id']}/documents",
                        files={"file": ("copy.pdf", fh, "application/pdf")}, data={"doc_type": "other"})
    assert r.status_code == 409 and r.json()["existing_id"] == doc["id"]
    # Another company may hold the same file.
    second = _company(client, name="Second Co")
    _upload(client, second["id"], "corvane-sustainability-update-2025")


def test_lost_files_report_410_and_reuploading_restores_them(client):
    from veridion.db import session_scope
    from veridion.models import Document
    from veridion.storage import get_storage

    register(client)
    company = _company(client)
    doc = _upload(client, company["id"], "corvane-sustainability-update-2025")
    run_pending()
    with session_scope() as s:
        key = s.get(Document, doc["id"]).storage_key
    get_storage().delete(key)  # what a restart on an ephemeral disk does

    gone = client.get(f"/api/v1/documents/{doc['id']}/pages/1/image")
    assert gone.status_code == 410 and gone.json()["code"] == "file_missing"
    restored = _upload(client, company["id"], "corvane-sustainability-update-2025")
    assert restored["id"] == doc["id"]
    assert client.get(f"/api/v1/documents/{doc['id']}/pages/1/image").status_code == 200


def test_full_workflow(client):
    register(client)
    company = _company(client)
    cid = company["id"]
    sr = _upload(client, cid, "aldermere-sustainability-report-2025")
    _upload(client, cid, "aldermere-annual-report-2025", doc_type="annual_report")
    assert sr["status"] == "uploaded" and sr["job"]["status"] == "queued"
    run_pending()

    docs = client.get(f"/api/v1/companies/{cid}/documents").json()
    assert {d["status"] for d in docs} == {"ready"}
    doc = client.get(f"/api/v1/documents/{sr['id']}").json()
    assert doc["page_count"] == 7 and doc["versions"][0]["version"] == 1
    image = client.get(f"/api/v1/documents/{sr['id']}/pages/4/image")
    assert image.status_code == 200 and image.headers["content-type"] == "image/png"
    passages = client.get(f"/api/v1/documents/{sr['id']}/passages", params={"page": 4}).json()
    assert any(p["metrics"] for p in passages)

    search = client.get("/api/v1/search", params={"company_id": cid, "q": "scope 1 emissions"}).json()
    assert search["results"] and search["results"][0]["match"]["terms"]

    sets = client.get("/api/v1/requirement-sets").json()
    statuses = {s["id"]: s["status"] for s in sets}
    assert statuses["gri-302-305-2016@1.1.0"] == "in_force" and statuses["gri-102-103-2025@0.1.0"] == "upcoming"

    r = client.post(f"/api/v1/companies/{cid}/runs", json={"requirement_set_id": "gri-302-305-2016@1.1.0",
                                                           "mode": "rules", "period_label": "FY2025"})
    assert r.status_code == 201, r.text
    run_id = r.json()["id"]
    hybrid = client.post(f"/api/v1/companies/{cid}/runs", json={"requirement_set_id": "gri-302-305-2016@1.1.0",
                                                                "mode": "hybrid"})
    assert hybrid.status_code == 400  # no model configured in tests
    run_pending()

    run = client.get(f"/api/v1/runs/{run_id}").json()
    assert run["status"] == "completed" and run["summary"]["requirements"] == 9
    findings = client.get(f"/api/v1/runs/{run_id}/findings").json()
    conflict = next(f for f in findings if f["requirement_code"] == "302-1")
    assert conflict["status"] == "conflicting" and conflict["primary_evidence"]["page"]

    trail = client.get(f"/api/v1/findings/{conflict['id']}").json()
    assert trail["requirement"]["display_code"] == "GRI 302-1"
    assert {e["role"] for e in trail["evidence"]} >= {"conflicting"}
    assert trail["actions"] and trail["actions"][0]["gap_key"] == "conflict:energy_total"

    bad = client.post(f"/api/v1/findings/{conflict['id']}/reviews", json={"decision": "override",
                                                                          "new_status": "supported"})
    assert bad.status_code == 422  # overrides need a reason
    ok = client.post(f"/api/v1/findings/{conflict['id']}/reviews", json={
        "decision": "override", "new_status": "supported", "note": "Finance confirmed 412,300 MWh is final."})
    assert ok.status_code == 201
    refreshed = client.get(f"/api/v1/runs/{run_id}/findings").json()
    reviewed = next(f for f in refreshed if f["id"] == conflict["id"])
    assert reviewed["review"]["state"] == "overridden" and reviewed["review"]["effective_status"] == "supported"
    assert reviewed["status"] == "conflicting"  # the original assessment is preserved

    actions = client.get(f"/api/v1/companies/{cid}/actions", params={"status": "open"}).json()
    patched = client.patch(f"/api/v1/actions/{actions[0]['id']}", json={"status": "in_progress", "owner": "CFO"})
    assert patched.status_code == 200 and patched.json()["owner"] == "CFO"

    for fmt, ctype in (("json", "application/json"), ("csv", "text/csv"), ("md", "text/markdown")):
        export = client.get(f"/api/v1/runs/{run_id}/export", params={"format": fmt})
        assert export.status_code == 200 and export.headers["content-type"].startswith(ctype)
    package = client.get(f"/api/v1/runs/{run_id}/export", params={"format": "json"}).json()
    assert package["format"] == "veridion.evidence-package/1" and package["documents"][0]["sha256"]

    overview = client.get(f"/api/v1/companies/{cid}/overview").json()
    assert overview["coverage"]["documents"] == 2 and overview["key_disclosures"]
    dash = client.get("/api/v1/dashboard").json()
    assert dash["contradictions"] and dash["material_gaps"]
    events = client.get("/api/v1/org/audit-events").json()
    assert {"assessment.started", "finding.override", "document.uploaded"} <= {e["action"] for e in events}


def test_plan_limits(client):
    register(client)  # explorer: 3 companies
    for i in range(3):
        _company(client, name=f"Company {i}")
    r = client.post("/api/v1/companies", json={"name": "One too many"})
    assert r.status_code == 402 and r.json()["code"] == "plan_limit"


def test_roles(client):
    register(client)
    r = client.post("/api/v1/org/members", json={"name": "Viewer", "email": "viewer@example.com", "role": "viewer"})
    assert r.status_code == 402  # explorer plan has one seat
    from veridion.db import session_scope
    from veridion.models import Organization

    with session_scope() as s:
        for o in s.query(Organization).all():
            o.plan = "professional"
    r = client.post("/api/v1/org/members", json={"name": "Viewer", "email": "viewer@example.com", "role": "viewer"})
    assert r.status_code == 201 and r.json()["temporary_password"]
    temp = r.json()["temporary_password"]
    client.cookies.clear()
    client.post("/api/v1/auth/login", json={"email": "viewer@example.com", "password": temp})
    assert client.post("/api/v1/companies", json={"name": "Not allowed"}).status_code == 403
    assert client.get("/api/v1/companies").status_code == 200


def test_public_enquiries_and_admin(client):
    r = client.post("/api/v1/public/enquiries", json={"kind": "demo_request", "name": "Visitor",
                                                      "email": "visitor@example.com",
                                                      "message": "We would like a walkthrough of the platform."})
    assert r.status_code == 201 and r.json()["reference"].startswith("ENQ-")
    bot = client.post("/api/v1/public/enquiries", json={"kind": "general", "name": "Bot", "email": "b@example.com",
                                                        "message": "Buy now buy now buy now", "website": "spam"})
    assert bot.status_code == 201
    register(client)
    assert client.get("/api/v1/admin/enquiries").status_code == 404
    client.cookies.clear()
    register(client, email="ops@veridion.test", org="Veridion Ops")
    enquiries = client.get("/api/v1/admin/enquiries").json()
    assert [e["kind"] for e in enquiries] == ["demo_request"]  # the honeypot submission was not stored
