# syntax=docker/dockerfile:1
#
# Veridion web (Next.js standalone server).
#
# The browser calls the API through this server (/api/* is rewritten to VERIDION_API_URL),
# so session cookies stay first-party. Rewrites are fixed when the image is built: pass the
# API's address inside your network as a build argument.

FROM node:24-bookworm-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund


FROM node:24-bookworm-slim AS build
WORKDIR /app
ARG VERIDION_API_URL=http://api:8000
ARG NEXT_PUBLIC_SITE_URL=http://localhost:3000
ENV VERIDION_API_URL=$VERIDION_API_URL \
    NEXT_PUBLIC_SITE_URL=$NEXT_PUBLIC_SITE_URL \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build


FROM node:24-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0
RUN groupadd --system --gid 10001 nextjs \
    && useradd --system --uid 10001 --gid nextjs --no-create-home --shell /usr/sbin/nologin nextjs
COPY --from=build --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nextjs /app/.next/static ./.next/static
COPY --from=build --chown=nextjs:nextjs /app/public ./public
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
