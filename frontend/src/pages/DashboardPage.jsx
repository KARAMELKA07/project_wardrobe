import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { fetchAnalyticsSummary } from "../api/analyticsApi";
import { fetchSavedOutfits } from "../api/outfitsApi";
import StatCard from "../components/StatCard";
import useAuth from "../hooks/useAuth";
import { translateCategory, translateSeason } from "../utils/i18n";


function renderSummaryLines(map, translateValue = (value) => value) {
  const entries = Object.entries(map || {});
  if (!entries.length) {
    return <p className="summary-line">Пока нет данных</p>;
  }

  return entries.map(([key, value]) => (
    <p key={key} className="summary-line">
      {translateValue(key)}: {value}
    </p>
  ));
}


export default function DashboardPage() {
  const { token } = useAuth();
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

  const seasonCoverage = Object.keys(analytics?.by_season || {}).length;
  const styleCoverage = Object.keys(analytics?.by_style || {}).length;
  const statusText = useMemo(() => {
    if (analytics?.recommendations?.length) {
      return analytics.recommendations[0];
    }

    return "Состав гардероба выглядит достаточно сбалансированным";
  }, [analytics]);

  return (
    <section className="page-section dashboard-page">
      <div className="section-heading section-heading-stack dashboard-heading">
        <div>
          <h1>Главная</h1>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <section className="overview-banner">
        <div className="overview-banner-copy">
          <p>{statusText}</p>
        </div>
        <div className="overview-banner-accent" />
      </section>

      <div className="stats-grid stats-grid-dashboard">
        <StatCard label="Количество вещей в гардеробе" value={analytics?.total_items ?? 0} />
        <StatCard label="Количество сохраненных образов" value={savedOutfitsCount} />
        <StatCard label="Покрыто сезонов" value={seasonCoverage} />
        <StatCard label="Покрыто стилей" value={styleCoverage} />
      </div>

      <Link to="/generate" className="primary-button primary-button-wide dashboard-cta">
        Подобрать образ
      </Link>

      <div className="summary-grid dashboard-summary-grid">
        <article className="summary-card dashboard-summary-card">
          <h3>По категориям</h3>
          <div className="summary-lines">
            {renderSummaryLines(analytics?.by_category, translateCategory)}
          </div>
        </article>

        <article className="summary-card dashboard-summary-card">
          <h3>По сезонам</h3>
          <div className="summary-lines">
            {renderSummaryLines(analytics?.by_season, translateSeason)}
          </div>
        </article>

        <article className="summary-card dashboard-summary-card">
          <h3>По стилям</h3>
          <div className="summary-lines">{renderSummaryLines(analytics?.by_style)}</div>
        </article>
      </div>
    </section>
  );
}
