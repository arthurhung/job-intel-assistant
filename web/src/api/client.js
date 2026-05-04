async function requestJson(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

export function fetchJobs() {
  return requestJson("/api/jobs");
}

export function fetchCrawlers() {
  return requestJson("/api/crawlers");
}

export function fetchMatchRuns() {
  return requestJson("/api/match-runs");
}

export function runCrawler(source = "all", allowedLocations = []) {
  return requestJson("/api/crawl", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source, allowed_locations: allowedLocations }),
  });
}

export function createMatches(payload) {
  return requestJson("/api/matches", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function parseResume(file) {
  return requestJson(`/api/resume/parse?filename=${encodeURIComponent(file.name)}`, {
    method: "POST",
    headers: { "Content-Type": file.type || "application/octet-stream" },
    body: file,
  });
}
