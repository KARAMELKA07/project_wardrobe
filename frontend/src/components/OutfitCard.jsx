import {
  getCategoryPlaceholderUrl,
  resolveItemImageUrl,
} from "../api/client";
import { getColorLabel } from "../data/clothingOptions";
import {
  translateCategory,
  translateEventType,
  translateFeatureName,
  translateRole,
} from "../utils/i18n";


export default function OutfitCard({ outfit, onSave, onReact, isSaved }) {
  return (
    <article className="card outfit-card">
      <div className="outfit-header">
        <div>
          <p className="eyebrow">{translateEventType(outfit.event_type) || "Образ"}</p>
          <h3>{outfit.name || "Сгенерированный образ"}</h3>
        </div>
        <span className="score-chip">Оценка {outfit.score}</span>
      </div>

      <p className="muted-text">{outfit.explanation}</p>

      {outfit.reasons?.length ? (
        <div className="stack-list">
          {outfit.reasons.map((reason) => (
            <div key={reason} className="list-chip">
              {reason}
            </div>
          ))}
        </div>
      ) : null}

      <div className="outfit-items">
        {(outfit.items || []).map((entry) => {
          const clothingItem = entry.clothing_item || entry || {};
          const itemId = entry.clothing_item_id || clothingItem.id;
          const itemRole = entry.role || clothingItem.category || "item";
          return (
            <div key={`${itemRole}-${itemId}`} className="outfit-item-row">
              <img
                src={resolveItemImageUrl(clothingItem, itemRole)}
                alt={clothingItem.title || itemRole}
                className="item-thumbnail"
                onError={(event) => {
                  event.currentTarget.src = getCategoryPlaceholderUrl(
                    clothingItem.category || itemRole,
                  );
                }}
              />

              <div>
                <strong>{clothingItem.title || "Без названия"}</strong>
                <p className="muted-text">
                  {translateRole(itemRole)}
                  {clothingItem.category ? ` | ${translateCategory(clothingItem.category)}` : ""}
                  {clothingItem.colors?.length
                    ? ` | ${clothingItem.colors.map(getColorLabel).join(", ")}`
                    : ""}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {outfit.feature_scores ? (
        <div className="feature-grid">
          {Object.entries(outfit.feature_scores).map(([name, value]) => (
            <div key={name} className="feature-badge">
              <span>{translateFeatureName(name)}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      ) : null}

      <div className="card-actions">
        {onSave ? (
          <button type="button" className="primary-button" onClick={() => onSave(outfit)}>
            {isSaved ? "Сохранено" : "Сохранить образ"}
          </button>
        ) : null}

        {onReact ? (
          <>
            <button
              type="button"
              className="secondary-button"
              onClick={() => onReact(outfit.id, "like")}
            >
              Нравится
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={() => onReact(outfit.id, "dislike")}
            >
              Не нравится
            </button>
          </>
        ) : null}
      </div>
    </article>
  );
}
