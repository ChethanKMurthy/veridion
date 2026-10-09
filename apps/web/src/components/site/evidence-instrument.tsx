import { StatusGlyph } from "@/components/ui/status";

// Visible by default. The reveal only runs when the inline script below marks the diagram as
// playable (visible tab, motion allowed), so crawlers, previews and paused tabs see the final state.
const css = `
.vi-play .vi-doc{animation:vi-fade .9s cubic-bezier(.25,1,.5,1) both}
.vi-play .vi-hl{animation:vi-fade .6s cubic-bezier(.25,1,.5,1) both}
.vi-play .vi-path{stroke-dasharray:420;animation:vi-draw 1.1s cubic-bezier(.25,1,.5,1) both}
.vi-play .vi-node{animation:vi-rise .7s cubic-bezier(.25,1,.5,1) both}
@keyframes vi-fade{from{opacity:0}}
@keyframes vi-draw{from{stroke-dashoffset:420}to{stroke-dashoffset:0}}
@keyframes vi-rise{from{opacity:0;transform:translateY(5px)}}
`;

const PLAY = `(function(){try{var s=document.getElementById("vi-instrument");if(s&&document.visibilityState==="visible"&&!window.matchMedia("(prefers-reduced-motion: reduce)").matches){s.classList.add("vi-play")}}catch(e){}})();`;

const delay = (s: number) => ({ animationDelay: `${s}s` });
const mono = { fontFamily: "var(--font-mono)" };
const sans = { fontFamily: "var(--font-sans)" };

function Lines({ x, ys, widths }: { x: number; ys: number[]; widths: number[] }) {
  return (
    <>
      {ys.map((y, i) => (
        <line key={y} x1={x} x2={x + widths[i % widths.length]} y1={y} y2={y} stroke="var(--color-rule-dark-strong)" strokeWidth="2.2" strokeLinecap="round" opacity="0.55" />
      ))}
    </>
  );
}

/**
 * The hero visual: a precise rendering of what Veridion does with one real (fictional-company)
 * finding — two documents disagree, both trace to a requirement, the conflict is assessed
 * and turned into an action.
 */
export function EvidenceInstrument({
  low = "412,300 MWh",
  high = "1,532,000 GJ",
  converted = "= 425,556 MWh",
  code = "GRI 302-1",
  difference = "3.2%",
}: {
  low?: string;
  high?: string;
  converted?: string;
  code?: string;
  difference?: string;
}) {
  return (
    <>
      <svg
        id="vi-instrument"
        suppressHydrationWarning
        viewBox="0 0 620 540"
        role="img"
        aria-labelledby="vi-title vi-desc"
        className="hidden h-auto w-full sm:block"
      >
        <title id="vi-title">How Veridion traces a finding to its sources</title>
        <desc id="vi-desc">
          A total energy figure of {low} on page 6 of a sustainability report and a figure of {high} on page 5 of the annual
          report both trace to requirement {code}. After converting units they differ by {difference}, so the assessment is
          conflicting evidence, which creates a reconciliation action.
        </desc>
        <style>{css}</style>

        {/* instrument scale */}
        <g opacity="0.5">
          {Array.from({ length: 30 }, (_, i) => (
            <line key={i} x1={16 + i * 20} x2={16 + i * 20} y1="12" y2={i % 5 === 0 ? 20 : 16} stroke="var(--color-rule-dark-strong)" strokeWidth="1" />
          ))}
        </g>
        <g style={mono} fontSize="10" fill="var(--color-on-dark-muted)">
          <text x="16" y="38">Sources</text>
          <text x="236" y="38">Evidence</text>
          <text x="430" y="38">Assessment</text>
        </g>

        {/* document A */}
        <g className="vi-doc" style={delay(0.1)}>
          <text x="16" y="62" style={mono} fontSize="9.5" fill="var(--color-on-dark-muted)">Sustainability report · p.6</text>
          <rect x="16" y="70" width="168" height="206" fill="var(--color-graphite)" stroke="var(--color-rule-dark-strong)" />
          <Lines x={28} ys={[88]} widths={[56]} />
          <line x1="28" x2="118" y1="102" y2="102" stroke="var(--color-on-dark-muted)" strokeWidth="3" strokeLinecap="round" opacity="0.7" />
          <Lines x={28} ys={[118, 128, 138]} widths={[144, 132, 98]} />
          <rect x="28" y="152" width="144" height="94" fill="none" stroke="var(--color-rule-dark-strong)" />
          {[167, 182, 197, 212, 227].map((y) => (
            <line key={y} x1="28" x2="172" y1={y} y2={y} stroke="var(--color-rule-dark)" />
          ))}
          <line x1="122" x2="122" y1="152" y2="246" stroke="var(--color-rule-dark)" />
          <line x1="148" x2="148" y1="152" y2="246" stroke="var(--color-rule-dark)" />
          <Lines x={34} ys={[160, 175, 190, 205, 220, 235]} widths={[70, 58, 64, 76, 52, 66]} />
          <Lines x={128} ys={[205]} widths={[14]} />
          <Lines x={28} ys={[260]} widths={[120]} />
        </g>
        <rect className="vi-hl" style={delay(1.0)} x="26" y="198" width="148" height="15" fill="oklch(0.72 0.08 85 / 0.22)" stroke="var(--color-brass)" strokeWidth="1.2" />

        {/* document B */}
        <g className="vi-doc" style={delay(0.35)}>
          <text x="40" y="306" style={mono} fontSize="9.5" fill="var(--color-on-dark-muted)">Annual report · p.5</text>
          <rect x="40" y="314" width="168" height="196" fill="var(--color-graphite)" stroke="var(--color-rule-dark-strong)" />
          <Lines x={52} ys={[332]} widths={[56]} />
          <line x1="52" x2="152" y1="346" y2="346" stroke="var(--color-on-dark-muted)" strokeWidth="3" strokeLinecap="round" opacity="0.7" />
          <Lines x={52} ys={[364, 374, 384]} widths={[144, 138, 112]} />
          <Lines x={52} ys={[404, 414]} widths={[146, 96]} />
          <Lines x={52} ys={[434, 444, 454, 464]} widths={[140, 144, 128, 70]} />
          <Lines x={52} ys={[484, 494]} widths={[136, 88]} />
        </g>
        <rect className="vi-hl" style={delay(1.9)} x="48" y="397" width="154" height="24" fill="oklch(0.66 0.11 27 / 0.2)" stroke="#c4766c" strokeWidth="1.2" />

        {/* evidence nodes */}
        <path className="vi-path" style={delay(1.2)} d="M174 205 C205 205 205 205 236 205" fill="none" stroke="var(--color-brass)" strokeWidth="1.2" />
        <g className="vi-node" style={delay(1.6)}>
          <rect x="236" y="184" width="132" height="42" rx="1.5" fill="var(--color-graphite)" stroke="var(--color-brass)" />
          <text x="248" y="202" style={sans} fontSize="13.5" fontWeight="500" fill="var(--color-on-dark)">{low}</text>
          <text x="248" y="217" style={mono} fontSize="9" fill="var(--color-on-dark-muted)">table row · FY2025</text>
        </g>
        <path className="vi-path" style={delay(2.1)} d="M202 409 C219 409 219 409 236 409" fill="none" stroke="#c4766c" strokeWidth="1.2" />
        <g className="vi-node" style={delay(2.5)}>
          <rect x="236" y="388" width="132" height="42" rx="1.5" fill="var(--color-graphite)" stroke="#c4766c" />
          <text x="248" y="406" style={sans} fontSize="13.5" fontWeight="500" fill="var(--color-on-dark)">{high}</text>
          <text x="248" y="421" style={mono} fontSize="9" fill="var(--color-on-dark-muted)">{converted}</text>
        </g>

        {/* requirement */}
        <g className="vi-node" style={delay(0.6)}>
          <rect x="430" y="80" width="176" height="70" rx="1.5" fill="var(--color-graphite)" stroke="var(--color-on-dark-muted)" />
          <text x="442" y="100" style={mono} fontSize="10" fill="var(--color-brass)">{code}</text>
          <text x="442" y="119" style={sans} fontSize="12.5" fill="var(--color-on-dark)">Energy consumption</text>
          <text x="442" y="135" style={sans} fontSize="12.5" fill="var(--color-on-dark)">within the organization</text>
        </g>
        <path className="vi-path" style={delay(2.9)} d="M368 205 C404 205 398 112 430 112" fill="none" stroke="var(--color-brass)" strokeWidth="1.2" />
        <path className="vi-path" style={delay(3.0)} d="M368 409 C412 409 394 132 430 132" fill="none" stroke="#c4766c" strokeWidth="1.2" />

        {/* assessment */}
        <path className="vi-path" style={delay(3.5)} d="M518 150 V236" fill="none" stroke="var(--color-on-dark-muted)" strokeWidth="1" />
        <g className="vi-node" style={delay(3.8)}>
          <rect x="430" y="236" width="176" height="58" rx="1.5" fill="var(--color-graphite)" stroke="#c4766c" />
          <path d="M448 251 455 258 448 265 441 258z" fill="none" stroke="#c4766c" strokeWidth="1.3" />
          <path d="m445.5 255.5 5 5M450.5 255.5l-5 5" stroke="#c4766c" strokeWidth="1.1" />
          <text x="462" y="262" style={sans} fontSize="12.5" fontWeight="500" fill="#d9928a">Conflicting evidence</text>
          <text x="442" y="282" style={mono} fontSize="9.5" fill="var(--color-on-dark-muted)">{difference} apart after conversion</text>
        </g>

        {/* action */}
        <path className="vi-path" style={delay(4.3)} d="M518 294 V380" fill="none" stroke="var(--color-on-dark-muted)" strokeWidth="1" />
        <g className="vi-node" style={delay(4.6)}>
          <rect x="430" y="380" width="176" height="58" rx="1.5" fill="var(--color-on-dark)" />
          <text x="442" y="402" style={sans} fontSize="12.5" fontWeight="500" fill="var(--color-obsidian)">Reconcile the two figures</text>
          <text x="442" y="421" style={mono} fontSize="9.5" fill="var(--color-ink-muted)">P = 1.0 × 0.8 × 0.8</text>
        </g>
        <text className="vi-node" style={{ ...delay(5), ...mono }} x="430" y="462" fontSize="9" fill="var(--color-on-dark-muted)">
          owner · due date · status · review
        </text>
      </svg>
      <script dangerouslySetInnerHTML={{ __html: PLAY }} />

      {/* Small screens: the same trail as readable text. */}
      <ol className="space-y-px overflow-hidden rounded-sm border border-rule-dark bg-rule-dark text-ui-sm sm:hidden" aria-label="How a finding is traced">
        {[
          ["Sources", `Sustainability report p.6: ${low}. Annual report p.5: ${high} (${converted.replace("= ", "")}).`],
          ["Requirement", `${code} · Energy consumption within the organization`],
          ["Assessment", `Conflicting evidence — ${difference} apart after unit conversion`],
          ["Action", "Reconcile the two figures and record any restatement"],
        ].map(([k, v], i) => (
          <li key={k} className="flex gap-3 bg-graphite px-4 py-3">
            <span className="tnum mt-0.5 inline-flex size-5 shrink-0 items-center justify-center rounded-full border border-rule-dark-strong text-[0.68rem] text-on-dark-muted">
              {i + 1}
            </span>
            <span>
              <span className="block text-meta text-on-dark-muted">{k}</span>
              <span className="mt-0.5 flex items-center gap-1.5 text-on-dark">
                {k === "Assessment" ? <StatusGlyph status="conflicting" className="text-[#c4766c]" /> : null}
                {v}
              </span>
            </span>
          </li>
        ))}
      </ol>
    </>
  );
}
