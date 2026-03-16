import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchAnalyticsSummary } from "../api/analyticsApi";
import { fetchSavedOutfits } from "../api/outfitsApi";
import StatCard from "../components/StatCard";
import useAuth from "../hooks/useAuth";


export default function DashboardPage() {
  const { token, user } = useAuth();
  const [analytics, setAnalytics] = useState(null);
  const [savedOutfitsCount, setSavedOutfitsCount] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [analyticsResponse, outfitsResponse] = await Promise.all([
          fetchAnalyticsSummary(token),
          fetchSavedOutfits(token),
        ]);
        setAnalytics(analyticsResponse);
        setSavedOutfitsCount(outfitsResponse.outfits.length);
      } catch (requestError) {
        setError(requestError.message);
      }
    }

    loadDashboard();
  }, [token]);

  const categoryCount = Object.keys(analytics?.by_category || {}).length;

  return (
    <section className="page-section">
      <div className="hero-card">
        <div>
          <p className="eyebrow">Главная</p>
          <h1 className="hero-title">
            {user?.name ? `${user.name}, ваш гардероб` : "Рабочее пространство гардероба"}
          </h1>
          <p className="muted-text">
            Используйте MVP для заполнения гардероба, генерации образов и проверки
            логики рекомендаций без LLM.
          </p>
        </div>

        <div className="hero-actions">
          <Link to="/wardrobe/add" className="primary-button">
            Добавить вещь
          </Link>
          <Link to="/generate" className="secondary-button">
            Подобрать образ
          </Link>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="stats-grid">
        <StatCard
          label="Вещи"
          value={analytics?.total_items ?? 0}
          helpText="Текущее количество вещей в гардеробе."
        />
        <StatCard
          label="Сохраненные образы"
          value={savedOutfitsCount}
          helpText="Количество сохраненных комбинаций."
        />
        <StatCard
          label="Категории"
          value={categoryCount}
          helpText="Сколько категорий уже представлено."
        />
      </div>

      <div className="two-column-grid">
        <article className="card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Быстрые действия</p>
              <h2>Что можно сделать дальше</h2>
            </div>
          </div>

          <div className="stack-list">
            <Link to="/wardrobe" className="list-link">
              Открыть гардероб
            </Link>
            <Link to="/generate" className="list-link">
              Запустить подбор образов
            </Link>
            <Link to="/analytics" className="list-link">
              Посмотреть аналитику
            </Link>
          </div>
        </article>

        <article className="card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Сводка</p>
              <h2>Рекомендации по гардеробу</h2>
            </div>
          </div>

          <div className="stack-list">
            {(analytics?.recommendations || ["Добавьте несколько вещей, чтобы появилась аналитика."]).map(
              (recommendation) => (
                <div key={recommendation} className="list-chip">
                  {recommendation}
                </div>
              ),
            )}
          </div>
        </article>
      </div>
    </section>
  );
}
