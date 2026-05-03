import { ControlPanel } from "./components/ControlPanel.jsx";
import { Header } from "./components/Header.jsx";
import { JobDetail } from "./components/JobDetail.jsx";
import { MatchList } from "./components/MatchList.jsx";
import { MatchRuns } from "./components/MatchRuns.jsx";
import { StatsBar } from "./components/StatsBar.jsx";
import { useDashboardData } from "./hooks/useDashboardData.js";

export function App() {
  const dashboard = useDashboardData();

  return (
    <main className="app-shell">
      <Header jobCount={dashboard.jobs.length} matchCount={dashboard.matches.length} />
      <section className="workspace">
        <ControlPanel {...dashboard} />
        <section className="results-panel">
          <StatsBar stats={dashboard.stats} minScore={dashboard.minScore} jobs={dashboard.jobs} />
          {dashboard.message ? <div className="status-line">{dashboard.message}</div> : null}
          <div className="results-grid">
            <MatchList
              matches={dashboard.filteredMatches}
              selectedJob={dashboard.selectedJob}
              setSelectedJob={dashboard.setSelectedJob}
            />
            <div className="side-stack">
              <JobDetail job={dashboard.selectedJob} />
              <MatchRuns runs={dashboard.matchRuns} />
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}
