import { useEffect, useState } from "react";

import { fetchCurrentWeather } from "../api/weatherApi";
import { resolveWeatherLocation } from "../utils/weatherLocation";


export default function useCurrentWeather(token, city) {
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let ignore = false;

    async function loadWeather() {
      if (!token) {
        if (!ignore) {
          setWeather(null);
        }
        return;
      }

      setLoading(true);
      try {
        const location = await resolveWeatherLocation();
        const response = await fetchCurrentWeather(token, location || {});
        if (!ignore) {
          setWeather(response.weather || null);
        }
      } catch {
        if (!ignore) {
          setWeather(null);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadWeather();

    return () => {
      ignore = true;
    };
  }, [token, city]);

  return {
    weather,
    loading,
  };
}
