import { cx } from "@/lib/format";

/**
 * A window onto a real (fictional-company) document page, centred on a cited passage.
 * Pure SVG: the viewBox crops the page image, so it scales with no JavaScript.
 */
export function PageCrop({
  src,
  size,
  bbox,
  role = "supporting",
  padY = 64,
  padX = 40,
  alt,
  className,
}: {
  src: string;
  size: [number, number];
  bbox: [number, number, number, number];
  role?: "supporting" | "conflicting";
  padY?: number;
  padX?: number;
  alt: string;
  className?: string;
}) {
  const [w, h] = size;
  const [x0, y0, x1, y1] = bbox;
  const vx = Math.max(0, x0 - padX);
  const vy = Math.max(0, y0 - padY);
  const vw = Math.min(w, x1 + padX) - vx;
  const vh = Math.min(h, y1 + padY) - vy;
  return (
    <svg viewBox={`${vx} ${vy} ${vw} ${vh}`} role="img" aria-label={alt} className={cx("block h-auto w-full overflow-hidden bg-white", className)}>
      <image href={src} x="0" y="0" width={w} height={h} preserveAspectRatio="none" />
      <rect
        x={x0 - 3}
        y={y0 - 3}
        width={x1 - x0 + 6}
        height={y1 - y0 + 6}
        rx="1.5"
        className="evidence-highlight"
        data-role={role === "conflicting" ? "conflicting" : undefined}
      />
    </svg>
  );
}
