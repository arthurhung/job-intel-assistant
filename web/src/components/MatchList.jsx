export function MatchList({ matches, selectedJob, setSelectedJob }) {
  if (!matches.length) {
    return (
      <div className="empty-state">
        <strong>No matches yet</strong>
        <p>Update jobs and match, or lower the score threshold.</p>
      </div>
    );
  }

  return (
    <div className="match-list">
      {matches.map((item, index) => (
        <button
          className={`match-row${selectedJob && selectedJob.url === item.url ? " active" : ""}`}
          key={`${item.company}-${item.title}-${index}`}
          type="button"
          onClick={() => setSelectedJob(item)}
        >
          <span className="rank">{index + 1}</span>
          <span className="match-main">
            <strong>{item.title}</strong>
            <small>{`${item.company} - ${item.location || "Remote/unspecified"}`}</small>
          </span>
          <span className="score">{item.score.toFixed(1)}</span>
        </button>
      ))}
    </div>
  );
}
