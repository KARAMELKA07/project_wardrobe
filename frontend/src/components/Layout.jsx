import { useMemo } from "react";
import { Link, Outlet } from "react-router-dom";

import useAuth from "../hooks/useAuth";
import useCurrentWeather from "../hooks/useCurrentWeather";
import clearWeatherIcon from "../icons/weather/clear.svg";
import cloudyWeatherIcon from "../icons/weather/cloudy.svg";
import rainWeatherIcon from "../icons/weather/rain.svg";
import snowWeatherIcon from "../icons/weather/snow.svg";
import sunnyWeatherIcon from "../icons/weather/sunny.svg";
import windWeatherIcon from "../icons/weather/wind.svg";
import { translateWeather } from "../utils/i18n";
import NavBar from "./NavBar";


function getWeatherIconAsset(condition) {
  switch (condition) {
    case "sunny":
      return sunnyWeatherIcon;
    case "clear":
      return clearWeatherIcon;
    case "rain":
      return rainWeatherIcon;
    case "snow":
      return snowWeatherIcon;
    case "wind":
      return windWeatherIcon;
    default:
      return cloudyWeatherIcon;
  }
}


export default function Layout() {
  const { token, user, logout } = useAuth();
  const { weather } = useCurrentWeather(token, user?.city);

  const cityLabel = weather?.city || user?.city || "Москва";
  const temperatureLabel =
    weather?.temperature === 0 || weather?.temperature
      ? `${weather.temperature} °C`
      : "— °C";
  const weatherLabel = weather?.weather_condition
    ? translateWeather(weather.weather_condition)
    : "Нет данных";
  const weatherIconSrc = useMemo(
    () => getWeatherIconAsset(weather?.weather_condition),
    [weather?.weather_condition],
  );

  return (
    <div className="app-shell">
      <NavBar />

      <main className="content-shell">
        <header className="topbar">
          <div className="weather-bar">
            <div className="weather-bar-city">{cityLabel}</div>
            <div className="weather-bar-temperature">{temperatureLabel}</div>
            <div className="weather-bar-icon-wrap">
              <img
                src={weatherIconSrc}
                alt={weatherLabel}
                className="weather-bar-icon-image"
              />
            </div>
            <div className="weather-bar-condition">{weatherLabel}</div>
          </div>

          <div className="topbar-actions">
            <Link to="/wardrobe/add" className="secondary-button topbar-add-button">
              Добавить вещь
            </Link>
            <button
              type="button"
              className="ghost-button topbar-logout-button"
              onClick={logout}
            >
              Выйти
            </button>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
}
