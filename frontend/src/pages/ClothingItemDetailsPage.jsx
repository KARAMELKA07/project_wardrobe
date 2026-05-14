import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { deleteItem, fetchItemById } from "../api/itemsApi";
import { getCategoryPlaceholderUrl, resolveItemImageUrl } from "../api/client";
import {
  getColorLabel,
  getFitLabel,
  getLayerLevelLabel,
  getStyleLabel,
  getSubcategoryLabel,
} from "../data/clothingOptions";
import useAuth from "../hooks/useAuth";
import { PencilIcon, TrashIcon } from "../icons/AppIcons";
import { translateCategory, translateFormality, translateSeason } from "../utils/i18n";


function formatItemValue(value, fallback = "Не указано") {
  return value || fallback;
}


export default function ClothingItemDetailsPage() {
  const { itemId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadItem() {
      try {
        const response = await fetchItemById(token, itemId);
        setItem(response.item);
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    }

    loadItem();
  }, [itemId, token]);

  async function handleDelete() {
    if (!itemId) {
      return;
    }

    if (!window.confirm("Удалить эту вещь из гардероба?")) {
      return;
    }

    setDeleting(true);
    setError("");

    try {
      await deleteItem(token, itemId);
      navigate("/wardrobe");
    } catch (requestError) {
      setError(requestError.message);
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <section className="page-section page-narrow">
        <div className="surface-card">Загрузка карточки вещи...</div>
      </section>
    );
  }

  if (!item) {
    return (
      <section className="page-section page-narrow">
        <div className="surface-card empty-state">
          <p className="error-text">{error || "Вещь не найдена."}</p>
          <Link to="/wardrobe" className="secondary-button">
            Вернуться в гардероб
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="page-section page-narrow">
      {error ? <p className="error-text">{error}</p> : null}

      <div className="item-detail-card">
        <img
          src={resolveItemImageUrl(item)}
          alt={item.title}
          className="item-detail-image"
          onError={(event) => {
            event.currentTarget.src = getCategoryPlaceholderUrl(item.category);
          }}
        />

        <div className="item-detail-content">
          <div className="item-detail-header">
            <div className="item-detail-title-block">
              <h1>{item.title}</h1>
              <p className="item-detail-subtitle">
                {translateCategory(item.category)}
                {item.subcategory ? ` | ${getSubcategoryLabel(item.subcategory)}` : ""}
              </p>
            </div>
            <span className="item-detail-season">{translateSeason(item.season)}</span>
          </div>

          <div className="item-detail-meta">
            <p>
              <strong>Цвета:</strong>{" "}
              {item.colors?.length ? item.colors.map(getColorLabel).join(", ") : "Не указаны"}
            </p>
            <p>
              <strong>Стили:</strong>{" "}
              {item.styles?.length ? item.styles.map(getStyleLabel).join(", ") : "Не указаны"}
            </p>
            <p>
              <strong>Формальность:</strong> {translateFormality(item.formality)}
            </p>
            <p>
              <strong>Посадка:</strong> {formatItemValue(getFitLabel(item.fit))}
            </p>
            <p>
              <strong>Слой:</strong> {formatItemValue(getLayerLevelLabel(item.layer_level))}
            </p>
            <p>
              <strong>Утепление:</strong> {item.insulation_rating ?? 0}
            </p>
            <p>
              <strong>Дождь:</strong> {item.waterproof ? "да" : "нет"}
            </p>
            <p>
              <strong>Ветер:</strong> {item.windproof ? "да" : "нет"}
            </p>
          </div>

          <div className="item-detail-actions">
            <Link
              to={`/wardrobe/${item.id}/edit`}
              className="icon-button icon-button-large"
              aria-label="Редактировать вещь"
              title="Редактировать"
            >
              <PencilIcon />
            </Link>
            <button
              type="button"
              className="icon-button icon-button-large"
              onClick={handleDelete}
              disabled={deleting}
              aria-label="Удалить вещь"
              title={deleting ? "Удаление..." : "Удалить"}
            >
              <TrashIcon />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
