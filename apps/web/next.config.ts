import type { NextConfig } from "next";

const API_URL = (process.env.VERIDION_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), interest-cohort=()" },
];

const nextConfig: NextConfig = {
  // A self-contained server for container deployments (see Dockerfile); ignored by hosts with their own build output.
  output: "standalone",
  cacheComponents: true,
  partialPrefetching: true,
  poweredByHeader: false,
  turbopack: {
    root: process.cwd(),
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  // The browser talks to the API through this same origin, so session cookies stay first-party.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
  // Planned information architecture: routes that are sections of other pages in version one.
  async redirects() {
    return [
      { source: "/solutions/company-intelligence", destination: "/intelligence", permanent: false },
      { source: "/solutions/evidence-analysis", destination: "/platform/evidence-explorer", permanent: false },
      { source: "/solutions/peer-benchmarking", destination: "/intelligence", permanent: false },
      { source: "/solutions", destination: "/platform", permanent: false },
      { source: "/company", destination: "/about", permanent: false },
      { source: "/contact/sales", destination: "/contact?topic=sales", permanent: false },
      { source: "/contact/support", destination: "/contact?topic=support", permanent: false },
      { source: "/contact/security", destination: "/trust/security#reporting", permanent: false },
      { source: "/legal/privacy", destination: "/legal/privacy-notice", permanent: false },
      { source: "/legal", destination: "/legal/terms", permanent: false },
      { source: "/login", destination: "/sign-in", permanent: false },
      { source: "/signup", destination: "/sign-up", permanent: false },
    ];
  },
  async headers() {
    return [
      { source: "/:path*", headers: securityHeaders },
      { source: "/demo/pages/:path*", headers: [{ key: "Cache-Control", value: "public, max-age=86400" }] },
    ];
  },
};

export default nextConfig;
