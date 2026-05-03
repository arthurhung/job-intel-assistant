import { Metric } from "./Metric.jsx";

export function Header({ jobCount, matchCount }) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Job Intel Assistant</p>
        <h1>Resume-to-job matching dashboard</h1>
      </div>
      <div className="topbar-metrics">
        <Metric label="Jobs" value={jobCount} />
        <Metric label="Matches" value={matchCount} />
      </div>
    </header>
  );
}
