import { apiFetch } from "./client";

export function fetchCurrentWeather(token) {
  return apiFetch("/weather/current", { token });
}
