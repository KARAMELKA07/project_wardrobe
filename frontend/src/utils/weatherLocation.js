const STORAGE_KEY = "wardrobe_weather_location";
const MAX_AGE_MS = 30 * 60 * 1000;


export function readStoredWeatherLocation(maxAgeMs = MAX_AGE_MS) {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const rawValue = window.localStorage.getItem(STORAGE_KEY);
    if (!rawValue) {
      return null;
    }

    const parsedValue = JSON.parse(rawValue);
    const isFresh = Date.now() - Number(parsedValue.timestamp || 0) <= maxAgeMs;
    if (!isFresh) {
      window.localStorage.removeItem(STORAGE_KEY);
      return null;
    }

    if (
      typeof parsedValue.latitude !== "number"
      || typeof parsedValue.longitude !== "number"
    ) {
      return null;
    }

    return {
      latitude: parsedValue.latitude,
      longitude: parsedValue.longitude,
    };
  } catch {
    return null;
  }
}


export function saveWeatherLocation(location) {
  if (
    typeof window === "undefined"
    || typeof location?.latitude !== "number"
    || typeof location?.longitude !== "number"
  ) {
    return;
  }

  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      latitude: location.latitude,
      longitude: location.longitude,
      timestamp: Date.now(),
    }),
  );
}


export function requestBrowserWeatherLocation() {
  if (typeof window === "undefined" || !window.navigator?.geolocation) {
    return Promise.resolve(null);
  }

  return new Promise((resolve) => {
    window.navigator.geolocation.getCurrentPosition(
      (position) => {
        const coordinates = {
          latitude: Number(position.coords.latitude),
          longitude: Number(position.coords.longitude),
        };
        saveWeatherLocation(coordinates);
        resolve(coordinates);
      },
      () => resolve(null),
      {
        enableHighAccuracy: false,
        timeout: 7000,
        maximumAge: MAX_AGE_MS,
      },
    );
  });
}


export async function resolveWeatherLocation({ allowPrompt = true } = {}) {
  const storedLocation = readStoredWeatherLocation();
  if (storedLocation) {
    return storedLocation;
  }

  if (!allowPrompt) {
    return null;
  }

  return requestBrowserWeatherLocation();
}
