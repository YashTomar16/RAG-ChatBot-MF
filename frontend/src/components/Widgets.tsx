import type { BootstrapData } from "../types";

export function PortfolioWidget({ portfolio }: { portfolio: BootstrapData["portfolio"] }) {
  const sign = portfolio.gain_positive ? "+" : "";
  return (
    <div className="card">
      <p className="caption">Demo Portfolio</p>
      <p className="portfolio-value">₹{portfolio.value.toLocaleString("en-IN")}</p>
      <p className={portfolio.gain_positive ? "gain-positive" : "gain-negative"}>
        {sign}₹{Math.abs(portfolio.gain).toLocaleString("en-IN")} ({portfolio.xirr}% XIRR)
      </p>
      <p className="footnote">
        Invested ₹{portfolio.invested.toLocaleString("en-IN")} · {portfolio.period}
      </p>
    </div>
  );
}

export function GoalCard({ goal }: { goal: BootstrapData["goal"] }) {
  return (
    <div className="card">
      <p className="caption">Goal Progress</p>
      <p className="fund-name">{goal.name}</p>
      <div className="progress-track" role="progressbar" aria-valuenow={goal.progress_pct}>
        <div className="progress-fill" style={{ width: `${goal.progress_pct}%` }} />
      </div>
      <p className="footnote">
        ₹{goal.current.toLocaleString("en-IN")} of ₹{goal.target.toLocaleString("en-IN")} · Target{" "}
        {goal.deadline}
      </p>
    </div>
  );
}

export function AllocationChart({
  allocation,
}: {
  allocation: BootstrapData["allocation"];
}) {
  let start = 0;
  const gradient = allocation
    .map(({ pct, color }) => {
      const end = start + pct;
      const part = `${color} ${start}% ${end}%`;
      start = end;
      return part;
    })
    .join(", ");

  return (
    <div className="card">
      <p className="section-title" style={{ fontSize: 18, marginBottom: 12 }}>
        Allocation
      </p>
      <div className="donut-wrap">
        <div
          className="donut"
          style={{ background: `conic-gradient(${gradient})` }}
          role="img"
          aria-label="Portfolio allocation chart"
        />
        <div>
          {allocation.map(({ label, pct, color }) => (
            <div className="legend-item" key={label}>
              <span className="legend-dot" style={{ background: color }} />
              <span>
                {label} · {pct}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function InsightCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="card glass">
      <p className="caption">AI Insight</p>
      <p className="fund-name">{title}</p>
      <p className="footnote" style={{ marginTop: 8 }}>
        {body}
      </p>
    </div>
  );
}
