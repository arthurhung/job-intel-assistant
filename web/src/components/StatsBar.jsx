import { Metric } from "./Metric.jsx";

export function StatsBar({ stats, minScore, jobs }) {
  return (
    <div className="stats-bar">
      <Metric label="Loaded jobs" value={jobs.length} />
      <Metric label={`Score >= ${minScore}`} value={stats.qualified} />
      <Metric label="Best score" value={stats.bestScore.toFixed(1)} />
    </div>
  );
}
