import type { BootstrapData, ChatResponse, HealthResponse, Product } from "../types";

const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, "") ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}

export function getBootstrap(): Promise<BootstrapData> {
  return request<BootstrapData>("/api/bootstrap");
}

export function getProducts(q = "", type = "all"): Promise<{ products: Product[]; count: number }> {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (type !== "all") params.set("type", type);
  const query = params.toString();
  return request(`/api/products${query ? `?${query}` : ""}`);
}

export function getProduct(id: number): Promise<{ product: Product }> {
  return request(`/api/products/${id}`);
}

export function compareProducts(a: number, b: number): Promise<{ fund_a: Product; fund_b: Product }> {
  return request(`/api/compare?a=${a}&b=${b}`);
}

export function postChat(question: string): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}
