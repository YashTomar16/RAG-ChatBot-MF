import type { Product } from "../types";

interface FundCardProps {
  product: Product;
  compact?: boolean;
  onClick?: () => void;
}

export function FundCard({ product, compact = false, onClick }: FundCardProps) {
  return (
    <div
      className="card fund-card"
      onClick={onClick}
      onKeyDown={onClick ? (e) => e.key === "Enter" && onClick() : undefined}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      style={onClick ? { cursor: "pointer" } : undefined}
    >
      <span className="badge">{product.product_type_label}</span>
      <p className="fund-name">{product.scheme_name}</p>
      <div className="price-row">
        <span className="price">{product.price_display}</span>
        <span className={`change ${product.change_direction}`}>{product.change_display}</span>
      </div>
      {!compact && product.expense_ratio_pct != null && (
        <p className="footnote">Expense ratio: {product.expense_ratio_pct}%</p>
      )}
      {!compact && (product.aum_display || product.market_cap_display) && (
        <p className="footnote">{product.aum_display ?? product.market_cap_display}</p>
      )}
    </div>
  );
}
