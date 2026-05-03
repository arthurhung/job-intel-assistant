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
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value);
  const normalized = value.includes("T") ? value : value.replace(" ", "T");
  const timestamp = hasTimezone ? normalized : `${normalized}Z`;
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-TW", {
    timeZone: "Asia/Taipei",
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(timestamp));
}
