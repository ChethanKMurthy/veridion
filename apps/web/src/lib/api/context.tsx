"use client";

import { createContext, useCallback, useContext, useMemo } from "react";
import useSWR, { SWRConfig, useSWRConfig, type SWRConfiguration } from "swr";
import type { DataClient, Params } from "./client";

const ClientContext = createContext<DataClient | null>(null);

export function DataProvider({ client, children }: { client: DataClient; children: React.ReactNode }) {
  return (
    <ClientContext.Provider value={client}>
      <SWRConfig
        value={{
          revalidateOnFocus: client.mode === "live",
          shouldRetryOnError: (err: unknown) => {
            const status = (err as { status?: number })?.status;
            return !status || status >= 500;
          },
          errorRetryCount: 2,
          keepPreviousData: true,
        }}
      >
        {children}
      </SWRConfig>
    </ClientContext.Provider>
  );
}

export function useClient(): DataClient {
  const client = useContext(ClientContext);
  if (!client) throw new Error("useClient must be used inside <DataProvider>");
  return client;
}

type Key = readonly [mode: string, path: string, params: string];

function keyFor(mode: string, path: string | null, params?: Params): Key | null {
  if (!path) return null;
  return [mode, path, JSON.stringify(params ?? {})] as const;
}

/** SWR-backed GET against the active client. Pass `null` as the path to skip. */
export function useApi<T>(path: string | null, params?: Params, options?: SWRConfiguration<T>) {
  const client = useClient();
  return useSWR<T>(
    keyFor(client.mode, path, params),
    ([, p]: Key) => client.get<T>(p, params),
    options,
  );
}

/** Revalidate every cached response whose path starts with one of the prefixes. */
export function useInvalidate() {
  const { mutate } = useSWRConfig();
  const client = useClient();
  return useCallback(
    (...prefixes: string[]) =>
      mutate(
        (key: unknown) =>
          Array.isArray(key) && key[0] === client.mode && prefixes.some((prefix) => String(key[1]).startsWith(prefix)),
        undefined,
        { revalidate: true },
      ),
    [mutate, client.mode],
  );
}

/** Build an in-product href under the active base ("/app" or "/demo"). */
export function useHref() {
  const client = useClient();
  return useMemo(() => (path: string) => `${client.base}${path === "/" ? "" : path}`, [client.base]);
}
