"use client";

import Link from "next/link";
import { useRef, useState, type DragEvent } from "react";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, Notice, SkeletonRows } from "@/components/ui/feedback";
import { Field, Input, Select } from "@/components/ui/field";
import { Document, Upload } from "@/components/ui/icons";
import { Dialog, IdTag, useToast } from "@/components/ui/overlay";
import { ApiError } from "@/lib/api/client";
import { useApi, useClient, useHref, useInvalidate } from "@/lib/api/context";
import type { DocumentInfo } from "@/lib/api/types";
import { DOC_TYPES, bytes, cx, date } from "@/lib/format";
import { PageHeader } from "../shell";
import { useCompanyId } from "../company-frame";

export function UploadDialog({
  open,
  onClose,
  companyId,
  replaces,
}: {
  open: boolean;
  onClose: () => void;
  companyId: string;
  replaces?: DocumentInfo | null;
}) {
  const client = useClient();
  const invalidate = useInvalidate();
  const toast = useToast();
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [docType, setDocType] = useState(replaces?.doc_type ?? "sustainability_report");
  const [period, setPeriod] = useState(replaces?.period_label ?? "FY2025");
  const [published, setPublished] = useState("");
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | Error | null>(null);

  const reset = () => {
    setFile(null);
    setTitle("");
    setError(null);
  };

  const pick = (f: File | undefined | null) => {
    if (!f) return;
    if (f.type !== "application/pdf" && !f.name.toLowerCase().endsWith(".pdf")) {
      setError(new Error("Only PDF files are supported."));
      return;
    }
    setError(null);
    setFile(f);
    if (!title) setTitle(f.name.replace(/\.pdf$/i, "").replace(/[-_]+/g, " "));
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    pick(e.dataTransfer.files?.[0]);
  };

  const submit = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.set("file", file);
      if (title.trim()) form.set("title", title.trim());
      form.set("doc_type", docType);
      if (period.trim()) form.set("period_label", period.trim());
      if (published) form.set("published_on", published);
      if (replaces) form.set("replaces", replaces.id);
      await client.upload(`/companies/${companyId}/documents`, form);
      await invalidate(`/companies/${companyId}`);
      toast(replaces ? "New version uploaded. Processing has started." : "Document uploaded. Processing has started.", "success");
      reset();
      onClose();
    } catch (err) {
      setError(err as Error);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={() => {
        reset();
        onClose();
      }}
      title={replaces ? "Upload a new version" : "Upload a document"}
      description={
        replaces
          ? `Replaces version ${replaces.version} of “${replaces.title}”. Earlier assessments keep citing the version they used.`
          : "PDF annual reports, sustainability reports, policies and data sheets. Scanned pages are read with OCR."
      }
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="primary" onClick={submit} loading={busy} disabled={!file}>
            Upload and process
          </Button>
        </>
      }
    >
      <div className="space-y-5">
        <button
          type="button"
          onClick={() => input.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={cx(
            "flex w-full flex-col items-center justify-center gap-2 rounded-sm border border-dashed px-6 py-8 text-center transition-colors",
            dragging ? "border-ink bg-shade" : "border-rule-strong bg-canvas hover:border-ink-muted",
          )}
        >
          <Upload size={20} className="text-ink-muted" />
          {file ? (
            <span className="text-ui text-ink">
              {file.name} <span className="text-ink-muted">· {bytes(file.size)}</span>
            </span>
          ) : (
            <span className="text-ui text-ink-muted">
              Drop a PDF here or <span className="font-medium text-ink underline underline-offset-2">choose a file</span>
            </span>
          )}
        </button>
        <input ref={input} type="file" accept="application/pdf,.pdf" className="sr-only" onChange={(e) => pick(e.target.files?.[0])} />

        <Field label="Title">{(p) => <Input {...p} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Sustainability Report 2025" />}</Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Document type">
            {(p) => (
              <Select {...p} value={docType} onChange={(e) => setDocType(e.target.value)}>
                {Object.entries(DOC_TYPES).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Reporting period" hint="Used when values appear without a year">
            {(p) => <Input {...p} value={period} onChange={(e) => setPeriod(e.target.value)} />}
          </Field>
        </div>
        <Field label="Publication date" optional>
          {(p) => <Input {...p} type="date" value={published} onChange={(e) => setPublished(e.target.value)} />}
        </Field>
        {error ? (
          <Notice tone={(error as ApiError).code === "plan_limit" ? "warning" : "danger"}>
            {error.message}{" "}
            {(error as ApiError).code === "demo_read_only" ? (
              <Link href="/request-access" className="font-medium text-ink underline underline-offset-2">
                Request access
              </Link>
            ) : null}
          </Notice>
        ) : null}
      </div>
    </Dialog>
  );
}

function ProcessingState({ doc }: { doc: DocumentInfo }) {
  if (doc.status === "ready") {
    return (
      <span className="text-ink-muted">
        <span className="tnum text-ink">{doc.stats.passages ?? 0}</span> passages · <span className="tnum text-ink">{doc.stats.metrics ?? 0}</span>{" "}
        values
        {doc.ocr_pages.length ? <> · OCR p.{doc.ocr_pages.join(", ")}</> : null}
      </span>
    );
  }
  if (doc.status === "failed") {
    return <span className="text-oxide">{doc.error ?? doc.job?.error ?? "Processing failed"}</span>;
  }
  const pct = doc.job?.progress?.pct ?? 5;
  return (
    <span className="block w-44" role="status">
      <span className="block text-ink">{doc.job?.progress?.message ?? "Queued for processing"}</span>
      <span className="mt-1 block h-1 overflow-hidden rounded-full bg-shade">
        <span className="block h-full bg-ink transition-[width] duration-500" style={{ width: `${Math.max(5, pct)}%` }} />
      </span>
    </span>
  );
}

export function DocumentsScreen() {
  const companyId = useCompanyId();
  const href = useHref();
  const client = useClient();
  const invalidate = useInvalidate();
  const toast = useToast();
  const [showAll, setShowAll] = useState(false);
  const [upload, setUpload] = useState<{ open: boolean; replaces?: DocumentInfo | null }>({ open: false });
  const { data: docs, error, mutate } = useApi<DocumentInfo[]>(
    `/companies/${companyId}/documents`,
    showAll ? { include_superseded: "true" } : undefined,
    { refreshInterval: (d) => (d?.some((x) => x.status === "uploaded" || x.status === "processing") ? 1500 : 0) },
  );

  const reprocess = async (doc: DocumentInfo) => {
    try {
      await client.send("POST", `/documents/${doc.id}/reprocess`);
      await invalidate(`/companies/${companyId}/documents`);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Could not reprocess", "danger");
    }
  };

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <PageHeader
        title="Documents"
        description="Every passage, table row and value is stored with its page and position, so findings can point to the exact source."
        actions={
          <>
            <label className="flex items-center gap-2 text-ui-sm text-ink-muted">
              <input type="checkbox" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} className="size-4 accent-[var(--color-ink)]" />
              Show replaced versions
            </label>
            <Button variant="primary" size="sm" icon={<Upload size={14} />} onClick={() => setUpload({ open: true })}>
              Upload
            </Button>
          </>
        }
      />
      <div className="mt-6 overflow-x-auto rounded-sm border border-rule bg-surface scrollbar-quiet">
        {error ? (
          <div className="p-4"><ErrorState error={error} retry={() => mutate()} /></div>
        ) : !docs ? (
          <div className="px-4"><SkeletonRows rows={4} /></div>
        ) : !docs.length ? (
          <EmptyState
            className="m-4 border-none"
            title="No documents yet"
            action={
              <Button variant="primary" icon={<Upload size={14} />} onClick={() => setUpload({ open: true })}>
                Upload a PDF
              </Button>
            }
          >
            Start with the most recent annual report and sustainability report. Add prior-year reports to see changes over time.
          </EmptyState>
        ) : (
          <table className="w-full min-w-[860px] text-left text-ui-sm">
            <thead>
              <tr className="border-b border-rule text-meta text-ink-muted">
                <th scope="col" className="px-4 py-2.5 font-medium">Document</th>
                <th scope="col" className="px-3 py-2.5 font-medium">Type</th>
                <th scope="col" className="px-3 py-2.5 font-medium">Period</th>
                <th scope="col" className="px-3 py-2.5 text-right font-medium">Pages</th>
                <th scope="col" className="px-3 py-2.5 font-medium">Extraction</th>
                <th scope="col" className="px-3 py-2.5 font-medium">Fingerprint</th>
                <th scope="col" className="px-4 py-2.5 font-medium"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id} className={cx("border-b border-rule align-top last:border-0", d.superseded_at && "bg-canvas")}>
                  <td className="max-w-[22rem] px-4 py-3">
                    <Link href={href(`/companies/${companyId}/documents/${d.id}`)} className="group flex items-start gap-2.5">
                      <Document className="mt-0.5 shrink-0 text-slate" />
                      <span className="min-w-0">
                        <span className="block font-medium text-ink group-hover:underline">{d.title}</span>
                        <span className="block truncate text-meta text-ink-muted">
                          {d.filename} · v{d.version} · {bytes(d.size_bytes)}
                          {d.superseded_at ? ` · replaced ${date(d.superseded_at)}` : ""}
                        </span>
                      </span>
                    </Link>
                  </td>
                  <td className="px-3 py-3 text-ink-muted">{DOC_TYPES[d.doc_type] ?? d.doc_type}</td>
                  <td className="px-3 py-3 text-ink-muted">{d.period_label ?? "—"}</td>
                  <td className="tnum px-3 py-3 text-right text-ink-muted">{d.page_count ?? "—"}</td>
                  <td className="px-3 py-3"><ProcessingState doc={d} /></td>
                  <td className="px-3 py-3"><IdTag value={d.sha256.slice(0, 12)} label="SHA-256 prefix" /></td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    {d.status === "failed" ? (
                      <Button size="sm" variant="secondary" onClick={() => reprocess(d)}>
                        Retry
                      </Button>
                    ) : !d.superseded_at ? (
                      <Button size="sm" variant="ghost" onClick={() => setUpload({ open: true, replaces: d })}>
                        New version
                      </Button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <UploadDialog
        key={upload.replaces?.id ?? "new"}
        open={upload.open}
        replaces={upload.replaces}
        companyId={companyId}
        onClose={() => setUpload({ open: false })}
      />
    </div>
  );
}
