import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { deleteItem, fetchItems } from "../api/itemsApi";
import {
  getCategoryPlaceholderUrl,
  resolveItemImageUrl,
} from "../api/client";
import {
  getColorLabel,
  getFitLabel,
  getLayerLevelLabel,
  getStyleLabel,
  getSubcategoryLabel,
} from "../data/clothingOptions";
import useAuth from "../hooks/useAuth";
import {
  translateCategory,
  translateFormality,
  translateSeason,
} from "../utils/i18n";


export default function WardrobePage() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadItems() {
      try {
        const response = await fetchItems(token);
        setItems(response.items);
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    }

    loadItems();
  }, [token]);

  async function handleDelete(itemId) {
    if (!window.confirm("Удалить эту вещь из гардероба?")) {
      return;
    }

    try {
      await deleteItem(token, itemId);
      setItems((currentItems) => currentItems.filter((item) => item.id !== itemId));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <section className="page-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Гардероб</p>
          <h1>Ваши вещи</h1>
        </div>
        <Link to="/wardrobe/add" className="primary-button">
          Добавить вещь
        </Link>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      {loading ? <div className="card">Загрузка гардероба...</div> : null}

      {!loading && items.length === 0 ? (
        <div className="card empty-state">
          Пока вещей нет. Добавьте верх, низ и обувь, чтобы начать подбор образов.
        </div>
      ) : null}

      <div className="item-grid">
        {items.map((item) => (
          <article key={item.id} className="card item-card">
            <img
              src={resolveItemImageUrl(item)}
              alt={item.title}
              className="item-cover"
              onError={(event) => {
                event.currentTarget.src = getCategoryPlaceholderUrl(item.category);
              }}
            />

            <div className="item-body">
              <div className="item-header">
                <div>
                  <h3>{item.title}</h3>
                  <p className="muted-text">
                    {translateCategory(item.category)}
                    {item.subcategory ? ` | ${getSubcategoryLabel(item.subcategory)}` : ""}
                  </p>
                </div>
                <span className="badge">{translateSeason(item.season)}</span>
              </div>

              <p className="muted-text">
                Цвета:
                {" "}
                {item.colors?.length
                  ? item.colors.map(getColorLabel).join(", ")
                  : "не указаны"}
              </p>
              <p className="muted-text">
                Стили:
                {" "}
                {item.styles?.length
                  ? item.styles.map(getStyleLabel).join(", ")
                  : "не указаны"}
              </p>
              <p className="muted-text">
                Формальность: {translateFormality(item.formality)}
              </p>
              <p className="muted-text">
                Посадка: {getFitLabel(item.fit) || "не указана"} | Слой:{" "}
                {getLayerLevelLabel(item.layer_level) || "не указан"}
              </p>
              <p className="muted-text">
                Утепление: {item.insulation_rating ?? 0} | Дождь:{" "}
                {item.waterproof ? "да" : "нет"} | Ветер: {item.windproof ? "да" : "нет"}
              </p>

              <div className="card-actions">
                <Link to={`/wardrobe/${item.id}/edit`} className="secondary-button">
                  Редактировать
                </Link>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => handleDelete(item.id)}
                >
                  Удалить
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
