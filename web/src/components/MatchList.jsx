const FEEDBACK_LABELS = {
  interested: "Good fit",
  ignored: "Not a fit",
  applied: "Applied",
};

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
            <span className="match-meta">
              <em>{item.source || "unknown source"}</em>
              {item.telegram_feedback ? (
                <span className={`feedback-badge ${item.telegram_feedback}`}>
                  {FEEDBACK_LABELS[item.telegram_feedback] || item.telegram_feedback}
                </span>
              ) : null}
            </span>
            <small>{`${item.company} - ${item.location || "Remote/unspecified"}`}</small>
          </span>
          <span className="score">
            {item.llm_score !== null && item.llm_score !== undefined
              ? item.llm_score.toFixed(1)
              : item.score.toFixed(1)}
          </span>
        </button>
      ))}
    </div>
  );
}
