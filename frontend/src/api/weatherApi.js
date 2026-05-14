import { apiFetch } from "./client";

export function fetchCurrentWeather(token, location = {}) {
  const searchParams = new URLSearchParams();
  if (typeof location.latitude === "number") {
    searchParams.set("latitude", String(location.latitude));
  }
  if (typeof location.longitude === "number") {
    searchParams.set("longitude", String(location.longitude));
  }

  const queryString = searchParams.toString();
  const path = queryString ? `/weather/current?${queryString}` : "/weather/current";
  return apiFetch(path, { token });
}
