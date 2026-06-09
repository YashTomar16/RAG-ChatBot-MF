import type { Product } from "../types";

interface ComparisonCardProps {
  fundA: Product;
  fundB: Product;
}

const FIELDS: Array<{
  label: string;
  value: (p: Product) => string;
}> = [
  { label: "NAV / Price", value: (p) => p.price_display },
  { label: "1D change", value: (p) => p.change_display },
  {
    label: "Expense ratio",
    value: (p) => (p.expense_ratio_pct != null ? `${p.expense_ratio_pct}%` : "—"),
  },
  {
    label: "AUM / Market cap",
    value: (p) => p.aum_display ?? p.market_cap_display ?? "—",
  },
];

export function ComparisonCard({ fundA, fundB }: ComparisonCardProps) {
  return (
    <div className="card">
      <div className="compare-grid" style={{ marginBottom: 12 }}>
        <div className="compare-header">{fundA.scheme_name}</div>
        <div className="compare-header">{fundB.scheme_name}</div>
      </div>
      {FIELDS.map(({ label, value }) => (
        <div className="compare-field" key={label}>
          <div className="compare-label">{label}</div>
          <div className="compare-grid">
            <div className="compare-value">{value(fundA)}</div>
            <div className="compare-value">{value(fundB)}</div>
          </div>
        </div>
      ))}
      <p className="footnote" style={{ marginTop: 12 }}>
        Factual comparison only — not a recommendation.
      </p>
    </div>
  );
}
