export function SkillGroup({ title, skills, tone }) {
  return (
    <section className="skill-group">
      <h3>{title}</h3>
      <div className="skill-list">
        {skills.length ? (
          skills.map((skill) => (
            <span className={`skill ${tone}`} key={skill}>
              {skill}
            </span>
          ))
        ) : (
          <span className="muted">None</span>
        )}
      </div>
    </section>
  );
}
