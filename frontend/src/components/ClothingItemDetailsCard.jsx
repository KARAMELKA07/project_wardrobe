import { Link } from "react-router-dom";

import { getCategoryPlaceholderUrl, resolveItemImageUrl } from "../api/client";
import {
  getColorLabel,
  getFitLabel,
  getLayerLevelLabel,
  getStyleLabel,
  getSubcategoryLabel,
} from "../data/clothingOptions";
import { PencilIcon, TrashIcon } from "../icons/AppIcons";
import { translateCategory, translateFormality, translateSeason } from "../utils/i18n";

function formatItemValue(value, fallback = "Не указано") {
  return value || fallback;
}

export default function ClothingItemDetailsCard({
  item,
  deleting = false,
  onDelete,
}) {
  return (
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
            <strong>Защита от дождя:</strong> {item.waterproof ? "да" : "нет"}
          </p>
          <p>
            <strong>Защита от ветра:</strong> {item.windproof ? "да" : "нет"}
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
            onClick={onDelete}
            disabled={deleting}
            aria-label="Удалить вещь"
            title={deleting ? "Удаление..." : "Удалить"}
          >
            <TrashIcon />
          </button>
        </div>
      </div>
    </div>
  );
}
