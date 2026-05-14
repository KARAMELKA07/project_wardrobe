import { useEffect, useState } from "react";
import { Link, Outlet } from "react-router-dom";

import { fetchCurrentWeather } from "../api/weatherApi";
import useAuth from "../hooks/useAuth";
import { CloudIcon } from "../icons/AppIcons";
import { translateWeather } from "../utils/i18n";
import NavBar from "./NavBar";


export default function Layout() {
  const { token, user, logout } = useAuth();
  const [weather, setWeather] = useState(null);

  useEffect(() => {
    let ignore = false;

    async function loadWeather() {
      try {
        const response = await fetchCurrentWeather(token);
        if (!ignore) {
          setWeather(response.weather || null);
        }
      } catch {
        if (!ignore) {
          setWeather(null);
        }
      }
    }

    if (token) {
      loadWeather();
    }

    return () => {
      ignore = true;
    };
  }, [token]);

  const cityLabel = weather?.city || user?.city || "Москва";
  const temperatureLabel =
    weather?.temperature === 0 || weather?.temperature
      ? `${weather.temperature} °C`
      : "12 °C";
  const weatherLabel = weather?.weather_condition
    ? translateWeather(weather.weather_condition)
    : "Облачно";

  return (
    <div className="app-shell">
      <NavBar />

      <main className="content-shell">
        <header className="topbar">
          <div className="weather-bar">
            <div className="weather-bar-city">{cityLabel}</div>
            <div className="weather-bar-temperature">{temperatureLabel}</div>
            <div className="weather-bar-icon-wrap">
              <CloudIcon className="weather-bar-icon" />
            </div>
            <div className="weather-bar-condition">{weatherLabel}</div>
          </div>

          <div className="topbar-actions">
            <Link to="/wardrobe/add" className="secondary-button topbar-add-button">
              Добавить вещь
            </Link>
            <button type="button" className="ghost-button topbar-logout-button" onClick={logout}>
              Выйти
            </button>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
}
