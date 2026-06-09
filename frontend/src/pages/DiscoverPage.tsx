import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getProduct, getProducts } from "../api/client";
import { FundCard } from "../components/FundCard";
import type { Product } from "../types";

const FILTERS = [
  { id: "all", label: "All" },
  { id: "mutual_fund", label: "Mutual Fund" },
  { id: "etf", label: "ETF" },
  { id: "stock", label: "Stock" },
] as const;

export function DiscoverPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["id"]>("all");
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getProducts(query, filter)
      .then((res) => setProducts(res.products))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, [query, filter]);

  return (
    <>
      <h1 className="large-title">Discover</h1>
      <input
        className="search-input"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search by name or type…"
        aria-label="Search funds"
      />
      <div className="segmented">
        {FILTERS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`btn btn-secondary${filter === item.id ? " active" : ""}`}
            onClick={() => setFilter(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      {loading ? (
        <div className="loading">Loading funds…</div>
      ) : (
        <div className="fund-grid">
          {products.map((product) => (
            <FundCard
              key={product.id}
              product={product}
              compact
              onClick={() => navigate(`/funds/${product.id}`)}
            />
          ))}
        </div>
      )}
      <div className="link-row">
        <button type="button" className="btn btn-secondary" onClick={() => navigate("/compare")}>
          Compare funds
        </button>
      </div>
    </>
  );
}

export function FundDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const productId = Number(id);
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!productId) return;
    setLoading(true);
    getProduct(productId)
      .then((res) => setProduct(res.product))
      .catch(() => setProduct(null))
      .finally(() => setLoading(false));
  }, [productId]);

  return (
    <>
      <button type="button" className="btn btn-secondary" onClick={() => navigate("/discover")}>
        ← Back to Discover
      </button>
      <h1 className="large-title">Fund Details</h1>
      {loading && <div className="loading">Loading fund…</div>}
      {!loading && !product && <div className="error-banner">Fund not found.</div>}
      {product && (
        <>
          <FundCard product={product} />
          <p className="footnote">
            <a href={product.source_url} target="_blank" rel="noopener noreferrer">
              View returns &amp; performance on Groww →
            </a>
          </p>
        </>
      )}
    </>
  );
}
