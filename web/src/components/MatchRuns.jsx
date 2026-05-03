export function MatchRuns({ runs }) {
  return (
    <section className="history-panel">
      <h3>Recent runs</h3>
      {runs.length ? (
        <div className="history-list">
          {runs.map((run) => (
            <div className="history-row" key={run.id}>
              <div>
                <strong>{`${run.qualified_matches}/${run.total_matches} qualified`}</strong>
                <small>{formatDate(run.created_at)}</small>
              </div>
              <span>{`min ${run.min_score.toFixed(1)}`}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="summary">No match runs recorded yet.</p>
      )}
    </section>
  );
}

function formatDate(value) {
  if (!value) return "-";
  const normalized = value.includes("T") ? value : value.replace(" ", "T");
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}
