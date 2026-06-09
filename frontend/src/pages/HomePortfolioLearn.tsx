import { useNavigate } from "react-router-dom";
import { AllocationChart, GoalCard, InsightCard, PortfolioWidget } from "../components/Widgets";
import { useBootstrap } from "../context/BootstrapContext";

export function HomePage() {
  const navigate = useNavigate();
  const bootstrap = useBootstrap();

  return (
    <>
      <h1 className="large-title">Home</h1>
      <PortfolioWidget portfolio={bootstrap.portfolio} />
      <GoalCard goal={bootstrap.goal} />
      <InsightCard
        title="Ask about HDFC schemes"
        body="Explore 12 HDFC funds, ETFs, and stocks with facts-only answers from Groww."
      />
      <button type="button" className="btn btn-primary" onClick={() => navigate("/chat")}>
        Ask AI
      </button>
    </>
  );
}

export function PortfolioPage() {
  const bootstrap = useBootstrap();

  return (
    <>
      <h1 className="large-title">Portfolio</h1>
      <p className="caption">Demo data — no login or PII collected</p>
      <PortfolioWidget portfolio={bootstrap.portfolio} />
      <AllocationChart allocation={bootstrap.allocation} />
      <InsightCard
        title="SIP calendar"
        body="Demo view — connect a broker account on Groww to manage real SIPs."
      />
    </>
  );
}

export function LearnPage() {
  const cards = [
    {
      title: "Understanding expense ratio",
      body: "The annual fee charged by a fund, expressed as a percentage of assets.",
    },
    {
      title: "What is exit load?",
      body: "A fee levied when you redeem units within a specified period.",
    },
    {
      title: "Risk categories",
      body: "SEBI-mandated riskometer levels from Low to Very High.",
    },
  ];

  return (
    <>
      <h1 className="large-title">Learn</h1>
      {cards.map((card) => (
        <div className="card" key={card.title}>
          <p className="fund-name">{card.title}</p>
          <p className="footnote">{card.body}</p>
        </div>
      ))}
      <div className="card glass">
        <p className="fund-name">Official resources</p>
        <p className="footnote" style={{ marginTop: 8 }}>
          <a href="https://www.amfiindia.com/investor-corner" target="_blank" rel="noopener noreferrer">
            AMFI Investor Corner
          </a>
          {" · "}
          <a href="https://investor.sebi.gov.in" target="_blank" rel="noopener noreferrer">
            SEBI Investor Education
          </a>
        </p>
      </div>
    </>
  );
}
