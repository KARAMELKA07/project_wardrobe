import { apiFetch } from "./client";


export function fetchAnalyticsSummary(token) {
  return apiFetch("/analytics/summary", {
    token,
  });
}
