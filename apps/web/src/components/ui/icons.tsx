/** Hand-drawn 1.5px stroke icon set on a 20px grid. Decorative unless a `title` is given. */

import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { title?: string; size?: number };

function Icon({ title, size = 16, children, ...rest }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={title ? undefined : true}
      role={title ? "img" : undefined}
      focusable="false"
      {...rest}
    >
      {title ? <title>{title}</title> : null}
      {children}
    </svg>
  );
}

export const ArrowRight = (p: IconProps) => (
  <Icon {...p}><path d="M4 10h12M11 5l5 5-5 5" /></Icon>
);
export const ArrowUpRight = (p: IconProps) => (
  <Icon {...p}><path d="M6 14 14 6M7 6h7v7" /></Icon>
);
export const ArrowLeft = (p: IconProps) => (
  <Icon {...p}><path d="M16 10H4M9 5l-5 5 5 5" /></Icon>
);
export const ChevronDown = (p: IconProps) => (
  <Icon {...p}><path d="m5 8 5 5 5-5" /></Icon>
);
export const ChevronRight = (p: IconProps) => (
  <Icon {...p}><path d="m8 5 5 5-5 5" /></Icon>
);
export const ChevronLeft = (p: IconProps) => (
  <Icon {...p}><path d="m12 5-5 5 5 5" /></Icon>
);
export const Close = (p: IconProps) => (
  <Icon {...p}><path d="m5 5 10 10M15 5 5 15" /></Icon>
);
export const Plus = (p: IconProps) => (
  <Icon {...p}><path d="M10 4v12M4 10h12" /></Icon>
);
export const Check = (p: IconProps) => (
  <Icon {...p}><path d="m4.5 10.5 3.5 3.5 7.5-8" /></Icon>
);
export const Search = (p: IconProps) => (
  <Icon {...p}><circle cx="8.75" cy="8.75" r="5.25" /><path d="m13 13 3.5 3.5" /></Icon>
);
export const Document = (p: IconProps) => (
  <Icon {...p}>
    <path d="M5 2.75h6.5L15 6.25v11H5z" />
    <path d="M11.5 2.75v3.5H15M7.5 10h5M7.5 13h5" />
  </Icon>
);
export const Upload = (p: IconProps) => (
  <Icon {...p}><path d="M10 13V3.5M6 7.5l4-4 4 4M3.5 13.5v3h13v-3" /></Icon>
);
export const Download = (p: IconProps) => (
  <Icon {...p}><path d="M10 3.5V13M6 9l4 4 4-4M3.5 13.5v3h13v-3" /></Icon>
);
export const Filter = (p: IconProps) => (
  <Icon {...p}><path d="M3 5h14M6 10h8M8.5 15h3" /></Icon>
);
export const Building = (p: IconProps) => (
  <Icon {...p}>
    <path d="M3.5 17V5.5l6.5-3 6.5 3V17M2 17h16" />
    <path d="M7 8.5v1.5M10 8.5v1.5M13 8.5v1.5M7 12.5V14M13 12.5V14M9 17v-3h2v3" />
  </Icon>
);
export const Layers = (p: IconProps) => (
  <Icon {...p}><path d="m10 3 7 3.75L10 10.5 3 6.75z" /><path d="m3 10.25 7 3.75 7-3.75M3 13.75l7 3.75 7-3.75" /></Icon>
);
export const Compare = (p: IconProps) => (
  <Icon {...p}><path d="M4 16V9M8 16V4M12 16v-5M16 16V7" /></Icon>
);
export const ListCheck = (p: IconProps) => (
  <Icon {...p}><path d="m3 5.5 1.5 1.5L7 4.5M3 13l1.5 1.5L7 12M10 6h7M10 13.5h7" /></Icon>
);
export const Clock = (p: IconProps) => (
  <Icon {...p}><circle cx="10" cy="10" r="7" /><path d="M10 6v4l2.5 2" /></Icon>
);
export const Grid = (p: IconProps) => (
  <Icon {...p}><path d="M3.5 3.5h5v5h-5zM11.5 3.5h5v5h-5zM3.5 11.5h5v5h-5zM11.5 11.5h5v5h-5z" /></Icon>
);
export const Settings = (p: IconProps) => (
  <Icon {...p}>
    <path d="M3 6h9M15 6h2M3 14h3M9 14h8" />
    <circle cx="13.5" cy="6" r="1.75" />
    <circle cx="7.5" cy="14" r="1.75" />
  </Icon>
);
export const Book = (p: IconProps) => (
  <Icon {...p}><path d="M3.5 4.5c2.5-1 4.5-.75 6.5.75v11c-2-1.5-4-1.75-6.5-.75zM16.5 4.5c-2.5-1-4.5-.75-6.5.75v11c2-1.5 4-1.75 6.5-.75z" /></Icon>
);
export const Shield = (p: IconProps) => (
  <Icon {...p}><path d="M10 2.75 16 5v5c0 3.75-2.5 6.25-6 7.25-3.5-1-6-3.5-6-7.25V5z" /></Icon>
);
export const Info = (p: IconProps) => (
  <Icon {...p}><circle cx="10" cy="10" r="7" /><path d="M10 9v4.5M10 6.5v.01" /></Icon>
);
export const Alert = (p: IconProps) => (
  <Icon {...p}><path d="M10 3 17.5 16h-15z" /><path d="M10 8v3.5M10 13.75v.01" /></Icon>
);
export const Eye = (p: IconProps) => (
  <Icon {...p}><path d="M2 10s3-5.5 8-5.5S18 10 18 10s-3 5.5-8 5.5S2 10 2 10z" /><circle cx="10" cy="10" r="2.25" /></Icon>
);
export const Link = (p: IconProps) => (
  <Icon {...p}><path d="M8.5 11.5a3 3 0 0 0 4.25 0l2.5-2.5a3 3 0 0 0-4.25-4.25l-1 1M11.5 8.5a3 3 0 0 0-4.25 0l-2.5 2.5a3 3 0 0 0 4.25 4.25l1-1" /></Icon>
);
export const Menu = (p: IconProps) => (
  <Icon {...p}><path d="M3 6h14M3 10h14M3 14h14" /></Icon>
);
export const SignOut = (p: IconProps) => (
  <Icon {...p}><path d="M8 3.5H4v13h4M12.5 6.5 16 10l-3.5 3.5M16 10H7.5" /></Icon>
);
export const History = (p: IconProps) => (
  <Icon {...p}><path d="M3.5 10a6.5 6.5 0 1 0 2-4.7" /><path d="M3 3.5v3h3M10 6.5V10l2.25 1.5" /></Icon>
);
export const Copy = (p: IconProps) => (
  <Icon {...p}><path d="M7 7h9v9.5H7z" /><path d="M13 4H4v9.5" /></Icon>
);
export const Sort = (p: IconProps) => (
  <Icon {...p}><path d="m6.5 8 3.5-3.5L13.5 8M6.5 12l3.5 3.5 3.5-3.5" /></Icon>
);
export const Play = (p: IconProps) => (
  <Icon {...p}><path d="M6.5 4.5v11l9-5.5z" /></Icon>
);
export const Printer = (p: IconProps) => (
  <Icon {...p}><path d="M5.5 7.5v-4h9v4M5.5 14H3.5V7.5h13V14h-2M5.5 11.5h9v5h-9z" /></Icon>
);
export const Target = (p: IconProps) => (
  <Icon {...p}><circle cx="10" cy="10" r="7" /><circle cx="10" cy="10" r="3.5" /><path d="M10 10h.01" /></Icon>
);
export const Spinner = ({ size = 16, ...p }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 20 20" aria-hidden="true" className="animate-spin" {...p}>
    <circle cx="10" cy="10" r="7" fill="none" stroke="currentColor" strokeOpacity="0.2" strokeWidth="2" />
    <path d="M17 10a7 7 0 0 0-7-7" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);
