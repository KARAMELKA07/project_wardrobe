import { useEffect, useState } from "react";

import { fetchAnalyticsSummary } from "../api/analyticsApi";
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


export default function AnalyticsPage() {
  const { token } = useAuth();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadSummary() {
      try {
        const response = await fetchAnalyticsSummary(token);
        setSummary(response);
      } catch (requestError) {
        setError(requestError.message);
      }
    }

    loadSummary();
  }, [token]);

  return (
    <section className="page-section analytics-page">
      <div className="section-heading section-heading-stack">
        <div>
          <h1>Аналитика гардероба</h1>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="stats-grid stats-grid-dashboard">
        <StatCard label="Всего вещей" value={summary?.total_items ?? 0} />
        <StatCard label="Покрыто сезонов" value={Object.keys(summary?.by_season || {}).length} />
        <StatCard label="Покрыто стилей" value={Object.keys(summary?.by_style || {}).length} />
      </div>

      <div className="summary-grid">
        <article className="summary-card">
          <h3>По категориям</h3>
          <div className="summary-lines">
            {renderSummaryLines(summary?.by_category, translateCategory)}
          </div>
        </article>

        <article className="summary-card">
          <h3>По сезонам</h3>
          <div className="summary-lines">
            {renderSummaryLines(summary?.by_season, translateSeason)}
          </div>
        </article>

        <article className="summary-card">
          <h3>По стилям</h3>
          <div className="summary-lines">{renderSummaryLines(summary?.by_style)}</div>
        </article>
      </div>
    </section>
  );
}
