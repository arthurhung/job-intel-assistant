import React, { useEffect, useMemo, useState } from "https://esm.sh/react@18.3.1";
import { createRoot } from "https://esm.sh/react-dom@18.3.1/client";

const e = React.createElement;

const SAMPLE_RESUME = [
  "Python backend engineer with experience in Airflow ETL pipelines, Docker deployments, PostgreSQL, Redis, SQL, AWS S3, data quality, web crawlers, and LLM workflow automation.",
  "Built production REST APIs with Flask and Django, maintained Linux services, and worked on reporting dashboards.",
].join("\n\n");

function App() {
  const [jobs, setJobs] = useState([]);
  const [matches, setMatches] = useState([]);
  const [matchRuns, setMatchRuns] = useState([]);
  const [resumeText, setResumeText] = useState(SAMPLE_RESUME);
  const [resumeFileName, setResumeFileName] = useState("");
  const [minScore, setMinScore] = useState(70);
  const [query, setQuery] = useState("");
  const [selectedJob, setSelectedJob] = useState(null);
  const [crawlerSources, setCrawlerSources] = useState(["remoteok"]);
  const [crawlerSource, setCrawlerSource] = useState("remoteok");
  const [notifyTelegram, setNotifyTelegram] = useState(false);
  const [telegramLimit, setTelegramLimit] = useState(5);
  const [loading, setLoading] = useState(false);
  const [crawling, setCrawling] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadJobs();
    loadCrawlers();
    loadMatchRuns();
  }, []);

  const filteredMatches = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return matches.filter((item) => {
      const passesScore = item.score >= Number(minScore);
      if (!normalized) return passesScore;
      return [
        item.title,
        item.company,
        item.location,
        item.matched_skills.join(" "),
        item.missing_skills.join(" "),
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalized);
    });
  }, [matches, minScore, query]);

  const stats = useMemo(() => {
    const bestScore = matches.length ? Math.max(...matches.map((item) => item.score)) : 0;
    const qualified = matches.filter((item) => item.score >= Number(minScore)).length;
    return { bestScore, qualified };
  }, [matches, minScore]);

  async function loadJobs() {
    setMessage("");
    const response = await fetch("/api/jobs");
    const data = await response.json();
    setJobs(data);
  }

  async function loadCrawlers() {
    const response = await fetch("/api/crawlers");
    const data = await response.json();
    const sources = data.sources || ["remoteok"];
    setCrawlerSources(sources);
    setCrawlerSource((current) => (sources.includes(current) ? current : sources[0] || "remoteok"));
  }

  async function loadMatchRuns() {
    const response = await fetch("/api/match-runs");
    const data = await response.json();
    setMatchRuns(data);
  }

  async function uploadResume(file) {
    if (!file) return;
    setUploadingResume(true);
    setMessage("");
    try {
      const body = await file.arrayBuffer();
      const response = await fetch(`/api/resume/parse?filename=${encodeURIComponent(file.name)}`, {
        method: "POST",
        headers: { "Content-Type": file.type || "application/octet-stream" },
        body,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Resume parse failed");
      }
      setResumeText(data.text);
      setResumeFileName(data.filename);
      setMessage(`Loaded ${data.char_count} character(s) from ${data.filename}.`);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setUploadingResume(false);
    }
  }

  async function runCrawl() {
    setCrawling(true);
    setMessage("");
    try {
      const response = await fetch("/api/crawl", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: crawlerSource }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Crawl request failed");
      }
      await loadJobs();
      setMessage(`Imported ${data.imported_count} job(s) from ${data.source}.`);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setCrawling(false);
    }
  }

  async function runMatch() {
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch("/api/matches", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText,
          notify_telegram: notifyTelegram,
          telegram_min_score: Number(minScore),
          telegram_limit: Number(telegramLimit),
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Match request failed");
      }
      setMatches(data.matches);
      setSelectedJob(data.matches[0] || null);
      await loadMatchRuns();
      const suffix =
        data.notified_count === null || data.notified_count === undefined
          ? ""
          : ` Telegram sent ${data.notified_count} item(s).`;
      setMessage(`Matched ${data.matches.length} job(s).${suffix}`);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  return e(
    "main",
    { className: "app-shell" },
    e(Header, { jobCount: jobs.length, matchCount: matches.length }),
    e(
      "section",
      { className: "workspace" },
      e(ControlPanel, {
        resumeText,
        setResumeText,
        resumeFileName,
        uploadResume,
        uploadingResume,
        minScore,
        setMinScore,
        query,
        setQuery,
        notifyTelegram,
        setNotifyTelegram,
        telegramLimit,
        setTelegramLimit,
        crawlerSources,
        crawlerSource,
        setCrawlerSource,
        crawling,
        runCrawl,
        loading,
        runMatch,
      }),
      e(
        "section",
        { className: "results-panel" },
        e(StatsBar, { stats, minScore, jobs }),
        message ? e("div", { className: "status-line" }, message) : null,
        e(
          "div",
          { className: "results-grid" },
          e(MatchList, {
            matches: filteredMatches,
            selectedJob,
            setSelectedJob,
          }),
          e(
            "div",
            { className: "side-stack" },
            e(JobDetail, { job: selectedJob }),
            e(MatchRuns, { runs: matchRuns })
          )
        )
      )
    )
  );
}

function Header({ jobCount, matchCount }) {
  return e(
    "header",
    { className: "topbar" },
    e(
      "div",
      null,
      e("p", { className: "eyebrow" }, "Job Intel Assistant"),
      e("h1", null, "Resume-to-job matching dashboard")
    ),
    e(
      "div",
      { className: "topbar-metrics" },
      e(Metric, { label: "Jobs", value: jobCount }),
      e(Metric, { label: "Matches", value: matchCount })
    )
  );
}

function Metric({ label, value }) {
  return e("div", { className: "metric" }, e("span", null, value), e("small", null, label));
}

function ControlPanel(props) {
  return e(
    "aside",
    { className: "control-panel" },
    e("label", { className: "field-label", htmlFor: "crawler-source" }, "Crawler source"),
    e(
      "div",
      { className: "action-row" },
      e(
        "select",
        {
          id: "crawler-source",
          value: props.crawlerSource,
          onChange: (event) => props.setCrawlerSource(event.target.value),
        },
        props.crawlerSources.map((source) => e("option", { key: source, value: source }, source))
      ),
      e(
        "button",
        {
          className: "secondary-button",
          type: "button",
          onClick: props.runCrawl,
          disabled: props.crawling,
        },
        props.crawling ? "Crawling..." : "Run crawl"
      )
    ),
    e(
      "label",
      { className: "upload-box" },
      e("span", null, props.uploadingResume ? "Parsing resume..." : "Upload resume"),
      e("small", null, props.resumeFileName || "PDF or TXT"),
      e("input", {
        type: "file",
        accept: ".pdf,.txt",
        onChange: (event) => props.uploadResume(event.target.files[0]),
        disabled: props.uploadingResume,
      })
    ),
    e("label", { className: "field-label", htmlFor: "resume" }, "Resume text"),
    e("textarea", {
      id: "resume",
      value: props.resumeText,
      onChange: (event) => props.setResumeText(event.target.value),
    }),
    e(
      "div",
      { className: "field-row" },
      e(
        "label",
        { className: "field-label", htmlFor: "min-score" },
        "Minimum score"
      ),
      e("output", null, props.minScore)
    ),
    e("input", {
      id: "min-score",
      type: "range",
      min: "0",
      max: "100",
      step: "5",
      value: props.minScore,
      onChange: (event) => props.setMinScore(event.target.value),
    }),
    e("label", { className: "field-label", htmlFor: "search" }, "Filter"),
    e("input", {
      id: "search",
      type: "search",
      placeholder: "Company, title, skill",
      value: props.query,
      onChange: (event) => props.setQuery(event.target.value),
    }),
    e(
      "label",
      { className: "toggle-row" },
      e("input", {
        type: "checkbox",
        checked: props.notifyTelegram,
        onChange: (event) => props.setNotifyTelegram(event.target.checked),
      }),
      e("span", null, "Send Telegram digest")
    ),
    e(
      "div",
      { className: "field-row compact" },
      e("label", { className: "field-label", htmlFor: "telegram-limit" }, "Telegram limit"),
      e("input", {
        id: "telegram-limit",
        type: "number",
        min: "1",
        max: "20",
        value: props.telegramLimit,
        onChange: (event) => props.setTelegramLimit(event.target.value),
      })
    ),
    e(
      "button",
      {
        className: "primary-button",
        type: "button",
        onClick: props.runMatch,
        disabled: props.loading || !props.resumeText.trim(),
      },
      props.loading ? "Matching..." : "Run match"
    )
  );
}

function StatsBar({ stats, minScore, jobs }) {
  return e(
    "div",
    { className: "stats-bar" },
    e(Metric, { label: "Loaded jobs", value: jobs.length }),
    e(Metric, { label: `Score >= ${minScore}`, value: stats.qualified }),
    e(Metric, { label: "Best score", value: stats.bestScore.toFixed(1) })
  );
}

function MatchList({ matches, selectedJob, setSelectedJob }) {
  if (!matches.length) {
    return e(
      "div",
      { className: "empty-state" },
      e("strong", null, "No matches yet"),
      e("p", null, "Run matching or lower the score threshold.")
    );
  }

  return e(
    "div",
    { className: "match-list" },
    matches.map((item, index) =>
      e(
        "button",
        {
          className:
            "match-row" + (selectedJob && selectedJob.url === item.url ? " active" : ""),
          key: `${item.company}-${item.title}-${index}`,
          type: "button",
          onClick: () => setSelectedJob(item),
        },
        e("span", { className: "rank" }, index + 1),
        e(
          "span",
          { className: "match-main" },
          e("strong", null, item.title),
          e("small", null, `${item.company} - ${item.location || "Remote/unspecified"}`)
        ),
        e("span", { className: "score" }, item.score.toFixed(1))
      )
    )
  );
}

function JobDetail({ job }) {
  if (!job) {
    return e(
      "article",
      { className: "detail-panel" },
      e("h2", null, "Select a match"),
      e("p", null, "The detail panel will show matched skills, missing skills, and a compact job summary.")
    );
  }

  return e(
    "article",
    { className: "detail-panel" },
    e("div", { className: "detail-header" }, e("h2", null, job.title), e("span", null, job.score.toFixed(1))),
    e("p", { className: "company-line" }, `${job.company} - ${job.location || "Remote/unspecified"}`),
    e(SkillGroup, { title: "Matched skills", skills: job.matched_skills, tone: "matched" }),
    e(SkillGroup, { title: "Missing skills", skills: job.missing_skills, tone: "missing" }),
    e("h3", null, "Summary"),
    e("p", { className: "summary" }, job.summary),
    job.url
      ? e("a", { className: "job-link", href: job.url, target: "_blank", rel: "noreferrer" }, "Open job")
      : null
  );
}

function MatchRuns({ runs }) {
  return e(
    "section",
    { className: "history-panel" },
    e("h3", null, "Recent runs"),
    runs.length
      ? e(
          "div",
          { className: "history-list" },
          runs.map((run) =>
            e(
              "div",
              { className: "history-row", key: run.id },
              e(
                "div",
                null,
                e("strong", null, `${run.qualified_matches}/${run.total_matches} qualified`),
                e("small", null, formatDate(run.created_at))
              ),
              e("span", null, `min ${run.min_score.toFixed(1)}`)
            )
          )
        )
      : e("p", { className: "summary" }, "No match runs recorded yet.")
  );
}

function formatDate(value) {
  if (!value) return "-";
  const normalized = value.includes("T") ? value : value.replace(" ", "T");
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function SkillGroup({ title, skills, tone }) {
  return e(
    "section",
    { className: "skill-group" },
    e("h3", null, title),
    e(
      "div",
      { className: "skill-list" },
      skills.length
        ? skills.map((skill) => e("span", { className: `skill ${tone}`, key: skill }, skill))
        : e("span", { className: "muted" }, "None")
    )
  );
}

createRoot(document.getElementById("root")).render(e(App));
