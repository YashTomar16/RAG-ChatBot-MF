import { useEffect, useState } from "react";
import { compareProducts, getProducts } from "../api/client";
import { ComparisonCard } from "../components/ComparisonCard";
import type { Product } from "../types";

export function ComparePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [idA, setIdA] = useState(4);
  const [idB, setIdB] = useState(2);
  const [comparison, setComparison] = useState<{ fund_a: Product; fund_b: Product } | null>(null);

  useEffect(() => {
    getProducts().then((res) => setProducts(res.products));
  }, []);

  useEffect(() => {
    if (!idA || !idB) return;
    compareProducts(idA, idB)
      .then(setComparison)
      .catch(() => setComparison(null));
  }, [idA, idB]);

  return (
    <>
      <h1 className="large-title">Compare</h1>
      <p className="footnote" style={{ marginBottom: 16 }}>
        Side-by-side factual fields — not investment advice.
      </p>
      <div className="compare-grid">
        <select
          className="select-input"
          value={idA}
          onChange={(e) => setIdA(Number(e.target.value))}
          aria-label="Fund A"
        >
          {products.map((p) => (
            <option key={p.id} value={p.id}>
              {p.scheme_name}
            </option>
          ))}
        </select>
        <select
          className="select-input"
          value={idB}
          onChange={(e) => setIdB(Number(e.target.value))}
          aria-label="Fund B"
        >
          {products.map((p) => (
            <option key={p.id} value={p.id}>
              {p.scheme_name}
            </option>
          ))}
        </select>
      </div>
      {comparison && <ComparisonCard fundA={comparison.fund_a} fundB={comparison.fund_b} />}
    </>
  );
}
