export type ChangeDirection = "gain" | "loss" | "neutral";

export interface Product {
  id: number;
  scheme_name: string;
  product_type: string;
  product_type_label: string;
  source_url: string;
  price_display: string;
  change_display: string;
  change_direction: ChangeDirection;
  expense_ratio_pct?: number;
  nav?: number;
  current_price?: number;
  change_1d_pct?: number;
  aum_cr?: number;
  market_cap_cr?: number;
  aum_display?: string | null;
  market_cap_display?: string | null;
  nav_date?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sourceUrl?: string | null;
  lastUpdated?: string | null;
  isRefusal?: boolean;
  product?: Product | null;
}

export interface ChatResponse {
  answer: string;
  source_url: string | null;
  last_updated: string | null;
  is_refusal: boolean;
  is_performance_deflection: boolean;
  product: Product | null;
  error?: string | null;
}

export interface BootstrapData {
  suggested_prompts: string[];
  portfolio: {
    value: number;
    invested: number;
    xirr: number;
    period: string;
    gain: number;
    gain_positive: boolean;
  };
  goal: {
    name: string;
    target: number;
    current: number;
    deadline: string;
    progress_pct: number;
  };
  allocation: Array<{ label: string; pct: number; color: string }>;
  index_ready: boolean;
  groq_configured: boolean;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  index_ready: boolean;
  groq_configured: boolean;
}

export type TabId = "home" | "discover" | "chat" | "portfolio" | "learn";
