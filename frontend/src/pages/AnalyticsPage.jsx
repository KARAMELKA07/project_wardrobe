import { useEffect, useState } from "react";

import { fetchAnalyticsSummary } from "../api/analyticsApi";
import StatCard from "../components/StatCard";
import useAuth from "../hooks/useAuth";
import { translateCategory, translateSeason } from "../utils/i18n";


function renderMapEntries(data, translateValue = (value) => value) {
  const entries = Object.entries(data || {});
  if (!entries.length) {
    return <div className="list-chip">Пока нет данных</div>;
  }

  return entries.map(([label, value]) => (
    <div key={label} className="list-chip">
      {translateValue(label)}: {value}
    </div>
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
    <section className="page-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Аналитика</p>
          <h1>Сводка по гардеробу</h1>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <div className="stats-grid">
        <StatCard
          label="Всего вещей"
          value={summary?.total_items ?? 0}
          helpText="Все вещи, добавленные текущим пользователем."
        />
        <StatCard
          label="Покрыто сезонов"
          value={Object.keys(summary?.by_season || {}).length}
          helpText="Сколько сезонов представлено в гардеробе."
        />
        <StatCard
          label="Покрыто стилей"
          value={Object.keys(summary?.by_style || {}).length}
          helpText="Сколько разных стилей есть в базе."
        />
      </div>

      <div className="two-column-grid">
        <article className="card">
          <p className="eyebrow">Категории</p>
          <h2>По категориям</h2>
          <div className="stack-list">
            {renderMapEntries(summary?.by_category, translateCategory)}
          </div>
        </article>

        <article className="card">
          <p className="eyebrow">Сезоны</p>
          <h2>По сезонам</h2>
          <div className="stack-list">
            {renderMapEntries(summary?.by_season, translateSeason)}
          </div>
        </article>

        <article className="card">
          <p className="eyebrow">Стили</p>
          <h2>По стилям</h2>
          <div className="stack-list">{renderMapEntries(summary?.by_style)}</div>
        </article>

        <article className="card">
          <p className="eyebrow">Рекомендации</p>
          <h2>Короткие выводы</h2>
          <div className="stack-list">
            {(summary?.recommendations || ["Аналитика появится после добавления вещей."]).map(
              (entry) => (
                <div key={entry} className="list-chip">
                  {entry}
                </div>
              ),
            )}
          </div>
        </article>
      </div>
    </section>
  );
}
