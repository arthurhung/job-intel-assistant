import { SkillGroup } from "./SkillGroup.jsx";

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
      <p className="company-line">{`${job.company} - ${job.location || "Remote/unspecified"}`}</p>
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
