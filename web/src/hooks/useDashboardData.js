import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createMatches,
  fetchJobs,
  fetchMatchRuns,
  parseResume,
  runCrawler,
} from "../api/client.js";
import { DEFAULT_CRAWLER_SOURCE, DEFAULT_RESUME, LOCATION_OPTIONS } from "../constants.js";

export function useDashboardData() {
  const [jobs, setJobs] = useState([]);
  const [matches, setMatches] = useState([]);
  const [matchRuns, setMatchRuns] = useState([]);
  const [resumeText, setResumeText] = useState(DEFAULT_RESUME);
  const [resumeFileName, setResumeFileName] = useState("");
  const [minScore, setMinScore] = useState(70);
  const [query, setQuery] = useState("");
  const [selectedJob, setSelectedJob] = useState(null);
  const [selectedLocations, setSelectedLocations] = useState(LOCATION_OPTIONS.map((option) => option.value));
  const [notifyTelegram, setNotifyTelegram] = useState(false);
  const [telegramLimit, setTelegramLimit] = useState(5);
  const [loading, setLoading] = useState(false);
  const [crawling, setCrawling] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [message, setMessage] = useState("");

  const loadJobs = useCallback(async () => {
    setJobs(await fetchJobs());
  }, []);

  const loadMatchRuns = useCallback(async () => {
    setMatchRuns(await fetchMatchRuns());
  }, []);

  useEffect(() => {
    Promise.all([loadJobs(), loadMatchRuns()]).catch((error) => {
      setMessage(error.message);
    });
  }, [loadJobs, loadMatchRuns]);

  const filteredMatches = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return matches.filter((item) => {
      const passesScore = item.score >= Number(minScore);
      if (!normalized) return passesScore;
      return [
        item.title,
        item.company,
        item.source,
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

  async function uploadResume(file) {
    if (!file) return;
    setUploadingResume(true);
    setMessage("");
    try {
      const data = await parseResume(file);
      setResumeText(data.text);
      setResumeFileName(data.filename);
      setMessage(`Loaded ${data.char_count} character(s) from ${data.filename}.`);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setUploadingResume(false);
    }
  }

  async function crawlSelectedJobs() {
    const data = await runCrawler(DEFAULT_CRAWLER_SOURCE, expandedLocationKeywords);
    await loadJobs();
    return data;
  }

  async function matchCurrentJobs() {
    const data = await createMatches({
      resume_text: resumeText,
      notify_telegram: notifyTelegram,
      telegram_min_score: Number(minScore),
      telegram_limit: Number(telegramLimit),
      allowed_locations: expandedLocationKeywords,
    });
    setMatches(data.matches);
    setSelectedJob(data.matches[0] || null);
    await loadMatchRuns();
    return data;
  }

  async function runMatch() {
    setLoading(true);
    setMessage("");
    try {
      const data = await matchCurrentJobs();
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

  async function runCrawlAndMatch() {
    setCrawling(true);
    setLoading(true);
    setMessage("");
    try {
      const crawlResult = await crawlSelectedJobs();
      const matchResult = await matchCurrentJobs();
      const suffix =
        matchResult.notified_count === null || matchResult.notified_count === undefined
          ? ""
          : ` Telegram sent ${matchResult.notified_count} item(s).`;
      const filtered =
        crawlResult.filtered_count > 0
          ? ` Skipped ${crawlResult.filtered_count} job(s) outside your location scope.`
          : "";
      setMessage(
        `Imported ${crawlResult.imported_count} job(s) from all sources.${filtered} Matched ${matchResult.matches.length} job(s).${suffix}`
      );
    } catch (error) {
      setMessage(error.message);
    } finally {
      setCrawling(false);
      setLoading(false);
    }
  }

  function toggleLocation(value) {
    setSelectedLocations((current) => {
      if (current.includes(value)) {
        return current.filter((item) => item !== value);
      }
      return [...current, value];
    });
  }

  const expandedLocationKeywords = useMemo(
    () =>
      selectedLocations.flatMap((value) =>
        value
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean)
      ),
    [selectedLocations]
  );

  return {
    jobs,
    matches,
    matchRuns,
    resumeText,
    setResumeText,
    resumeFileName,
    minScore,
    setMinScore,
    query,
    setQuery,
    selectedJob,
    setSelectedJob,
    locationOptions: LOCATION_OPTIONS,
    selectedLocations,
    toggleLocation,
    notifyTelegram,
    setNotifyTelegram,
    telegramLimit,
    setTelegramLimit,
    loading,
    crawling,
    uploadingResume,
    message,
    filteredMatches,
    stats,
    uploadResume,
    runMatch,
    runCrawlAndMatch,
  };
}
