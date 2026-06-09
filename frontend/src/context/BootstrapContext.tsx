import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { getBootstrap } from "../api/client";
import type { BootstrapData } from "../types";

const BootstrapContext = createContext<BootstrapData | null>(null);

export function BootstrapProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<BootstrapData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getBootstrap()
      .then(setData)
      .catch((err: Error) => setError(err.message));
  }, []);

  if (error) {
    return <div className="error-banner">Failed to load app data: {error}</div>;
  }

  if (!data) {
    return <div className="loading">Loading…</div>;
  }

  return <BootstrapContext.Provider value={data}>{children}</BootstrapContext.Provider>;
}

export function useBootstrap() {
  const ctx = useContext(BootstrapContext);
  if (!ctx) throw new Error("useBootstrap must be used within BootstrapProvider");
  return ctx;
}
