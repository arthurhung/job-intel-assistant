import { SkillGroup } from "./SkillGroup.jsx";

const FEEDBACK_LABELS = {
  interested: "Good fit",
  ignored: "Not a fit",
  applied: "Applied",
};

export function JobDetail({ job }) {
  if (!job) {
    return (
      <article className="detail-panel">
        <h2>Select a match</h2>
        <p>The detail panel will show matched skills, missing skills, and a compact job summary.</p>
      </article>
    );
  }

  return (
    <article className="detail-panel">
      <div className="detail-header">
        <h2>{job.title}</h2>
        <span>{job.score.toFixed(1)}</span>
      </div>
      <div className="detail-chips">
        <div className="source-chip">{job.source || "unknown source"}</div>
        {job.telegram_feedback ? (
          <div className={`feedback-badge ${job.telegram_feedback}`}>
            {FEEDBACK_LABELS[job.telegram_feedback] || job.telegram_feedback}
          </div>
        ) : null}
      </div>
      <p className="company-line">{`${job.company} - ${job.location || "Remote/unspecified"}`}</p>
      {job.telegram_feedback_updated_at ? (
        <p className="feedback-note">Telegram feedback updated at {job.telegram_feedback_updated_at}</p>
      ) : null}
      {job.llm_score !== null && job.llm_score !== undefined ? (
        <section className="llm-panel">
          <h3>LLM Fit</h3>
          <strong>{job.llm_score.toFixed(1)}</strong>
          <p>{job.llm_recommendation || "No LLM recommendation provided."}</p>
          {job.llm_concerns?.length ? (
            <ul>
              {job.llm_concerns.map((concern) => (
                <li key={concern}>{concern}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}
      <SkillGroup title="Matched skills" skills={job.matched_skills} tone="matched" />
      <SkillGroup title="Missing skills" skills={job.missing_skills} tone="missing" />
      <h3>Summary</h3>
      <p className="summary">{job.summary}</p>
      {job.url ? (
        <a className="job-link" href={job.url} target="_blank" rel="noreferrer">
          Open job
        </a>
      ) : null}
    </article>
  );
}
