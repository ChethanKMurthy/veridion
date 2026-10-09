"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useClient } from "@/lib/api/context";
import { cx } from "@/lib/format";

export type Highlight = {
  id: string;
  bbox: [number, number, number, number];
  role?: "supporting" | "conflicting" | "related" | "active" | "search";
  label?: string;
};

/**
 * A rendered PDF page with highlight rectangles drawn in PDF point space, so the
 * overlay stays exact at any display size. Clicking a highlight selects it.
 */
export function PageView({
  documentId,
  page,
  pageSize,
  highlights = [],
  activeId,
  onSelect,
  className,
  focusActive = false,
  alt,
}: {
  documentId: string;
  page: number;
  pageSize: [number, number] | undefined;
  highlights?: Highlight[];
  activeId?: string | null;
  onSelect?: (id: string) => void;
  className?: string;
  focusActive?: boolean;
  alt?: string;
}) {
  const client = useClient();
  const [loadedSrc, setLoadedSrc] = useState<string | null>(null);
  const [failedSrc, setFailedSrc] = useState<string | null>(null);
  const activeRef = useRef<SVGRectElement | null>(null);
  const [w, h] = pageSize ?? [595, 842];
  const src = client.pageImageUrl(documentId, page);
  const loaded = loadedSrc === src;
  const failed = failedSrc === src;

  useEffect(() => {
    if (!focusActive || !loaded || !activeRef.current) return;
    activeRef.current.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [activeId, loaded, focusActive]);

  return (
    <div
      className={cx("relative w-full overflow-hidden bg-white shadow-[0_0_0_1px_var(--color-rule)]", className)}
      style={{ aspectRatio: `${w} / ${h}` }}
    >
      {!loaded && !failed ? <div className="absolute inset-0 animate-pulse bg-shade" aria-hidden="true" /> : null}
      {failed ? (
        <div className="absolute inset-0 flex items-center justify-center p-6 text-center text-ui-sm text-ink-muted">
          The page image could not be loaded.
        </div>
      ) : null}
      {/* eslint-disable-next-line @next/next/no-img-element -- authenticated API image, not optimisable */}
      <img
        src={src}
        alt={alt ?? `Page ${page}`}
        className={cx("absolute inset-0 size-full select-none transition-opacity duration-200", loaded ? "opacity-100" : "opacity-0")}
        onLoad={() => setLoadedSrc(src)}
        onError={() => setFailedSrc(src)}
        draggable={false}
      />
      <svg viewBox={`0 0 ${w} ${h}`} className="absolute inset-0 size-full" preserveAspectRatio="none">
        {highlights.map((hl) => {
          const [x0, y0, x1, y1] = hl.bbox;
          const active = hl.id === activeId;
          const pad = 2.5;
          return (
            <rect
              key={`${hl.id}-${hl.role}`}
              ref={active ? activeRef : undefined}
              x={x0 - pad}
              y={y0 - pad}
              width={x1 - x0 + pad * 2}
              height={y1 - y0 + pad * 2}
              rx={1.5}
              className="evidence-highlight"
              data-role={hl.role === "active" ? undefined : hl.role}
              style={{ opacity: activeId && !active ? 0.45 : 1, cursor: onSelect ? "pointer" : undefined, strokeWidth: active ? 2 : 1.25 }}
              onClick={onSelect ? () => onSelect(hl.id) : undefined}
            >
              {hl.label ? <title>{hl.label}</title> : null}
            </rect>
          );
        })}
      </svg>
    </div>
  );
}

/**
 * A magnified window onto part of a page, centred on the active passage. Used in the
 * evidence trail so the cited text is readable without leaving the inspector.
 * The excerpt pans inside its own frame and never scrolls the surrounding page.
 */
export function PageExcerpt({
  documentId,
  page,
  pageSize,
  highlights,
  activeId,
  onSelect,
  height = 300,
  zoom = 1.35,
  alt,
}: {
  documentId: string;
  page: number;
  pageSize: [number, number] | undefined;
  highlights: Highlight[];
  activeId: string | null | undefined;
  onSelect?: (id: string) => void;
  height?: number;
  zoom?: number;
  alt?: string;
}) {
  const client = useClient();
  const frame = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  const [loadedSrc, setLoadedSrc] = useState<string | null>(null);
  const [w, h] = pageSize ?? [595, 842];
  const src = client.pageImageUrl(documentId, page);
  const loaded = loadedSrc === src;

  useLayoutEffect(() => {
    const el = frame.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    ro.observe(el);
    setWidth(el.getBoundingClientRect().width);
    return () => ro.disconnect();
  }, []);

  const scale = width ? (width * zoom) / w : 0;
  const active = highlights.find((hl) => hl.id === activeId) ?? highlights[0];
  let tx = 0;
  let ty = 0;
  if (active && scale) {
    const [x0, y0, x1, y1] = active.bbox;
    const cx = ((x0 + x1) / 2) * scale;
    const cy = ((y0 + y1) / 2) * scale;
    tx = Math.min(0, Math.max(width - w * scale, width / 2 - cx));
    ty = Math.min(0, Math.max(height - h * scale, height / 2 - cy));
  }

  return (
    <div
      ref={frame}
      className="relative w-full overflow-hidden bg-white shadow-[0_0_0_1px_var(--color-rule)]"
      style={{ height }}
    >
      {!loaded ? <div className="absolute inset-0 animate-pulse bg-shade" aria-hidden="true" /> : null}
      {scale ? (
        <div
          className="absolute left-0 top-0 origin-top-left transition-transform duration-300 ease-[var(--ease-out-quart)]"
          style={{ width: w * scale, height: h * scale, transform: `translate(${tx}px, ${ty}px)` }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element -- authenticated API image */}
          <img
            src={src}
            alt={alt ?? `Page ${page}`}
            className={cx("absolute inset-0 size-full select-none", loaded ? "opacity-100" : "opacity-0")}
            onLoad={() => setLoadedSrc(src)}
            draggable={false}
          />
          <svg viewBox={`0 0 ${w} ${h}`} className="absolute inset-0 size-full" preserveAspectRatio="none">
            {highlights.map((hl) => {
              const [x0, y0, x1, y1] = hl.bbox;
              const isActive = hl.id === active?.id;
              return (
                <rect
                  key={`${hl.id}-${hl.role}`}
                  x={x0 - 2.5}
                  y={y0 - 2.5}
                  width={x1 - x0 + 5}
                  height={y1 - y0 + 5}
                  rx={1.5}
                  className="evidence-highlight"
                  data-role={hl.role === "active" ? undefined : hl.role}
                  style={{ opacity: isActive ? 1 : 0.4, strokeWidth: isActive ? 1.6 : 1, cursor: onSelect ? "pointer" : undefined }}
                  onClick={onSelect ? () => onSelect(hl.id) : undefined}
                >
                  {hl.label ? <title>{hl.label}</title> : null}
                </rect>
              );
            })}
          </svg>
        </div>
      ) : null}
    </div>
  );
}
