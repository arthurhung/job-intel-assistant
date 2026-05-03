export function ControlPanel({
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
  runCrawlAndMatch,
}) {
  const isBusy = crawling || loading;

  return (
    <aside className="control-panel">
      <label className="field-label" htmlFor="crawler-source">
        Crawler source
      </label>
      <div className="action-row">
        <select
          id="crawler-source"
          value={crawlerSource}
          onChange={(event) => setCrawlerSource(event.target.value)}
        >
          {crawlerSources.map((source) => (
            <option key={source} value={source}>
              {source}
            </option>
          ))}
        </select>
        <button className="secondary-button" type="button" onClick={runCrawl} disabled={isBusy}>
          {crawling ? "Crawling..." : "Run crawl"}
        </button>
      </div>
      <label className="upload-box">
        <span>{uploadingResume ? "Parsing resume..." : "Upload resume"}</span>
        <small>{resumeFileName || "PDF or TXT"}</small>
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={(event) => uploadResume(event.target.files[0])}
          disabled={uploadingResume}
        />
      </label>
      <label className="field-label" htmlFor="resume">
        Resume text
      </label>
      <textarea
        id="resume"
        value={resumeText}
        onChange={(event) => setResumeText(event.target.value)}
      />
      <div className="field-row">
        <label className="field-label" htmlFor="min-score">
          Minimum score
        </label>
        <output>{minScore}</output>
      </div>
      <input
        id="min-score"
        type="range"
        min="0"
        max="100"
        step="5"
        value={minScore}
        onChange={(event) => setMinScore(event.target.value)}
      />
      <label className="field-label" htmlFor="search">
        Filter
      </label>
      <input
        id="search"
        type="search"
        placeholder="Company, title, skill"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      <label className="toggle-row">
        <input
          type="checkbox"
          checked={notifyTelegram}
          onChange={(event) => setNotifyTelegram(event.target.checked)}
        />
        <span>Send Telegram digest</span>
      </label>
      <div className="field-row compact">
        <label className="field-label" htmlFor="telegram-limit">
          Telegram limit
        </label>
        <input
          id="telegram-limit"
          type="number"
          min="1"
          max="20"
          value={telegramLimit}
          onChange={(event) => setTelegramLimit(event.target.value)}
        />
      </div>
      <button
        className="primary-button"
        type="button"
        onClick={runMatch}
        disabled={loading || !resumeText.trim()}
      >
        {loading ? "Matching..." : "Run match"}
      </button>
      <button
        className="tertiary-button"
        type="button"
        onClick={runCrawlAndMatch}
        disabled={isBusy || !resumeText.trim()}
      >
        Crawl + match
      </button>
    </aside>
  );
}
