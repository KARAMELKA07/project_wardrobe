import { useMemo, useRef } from "react";
import { Link } from "react-router-dom";

import {
  getCategoryPlaceholderUrl,
  resolveAssetUrl,
  resolveItemImageUrl,
} from "../api/client";
import { translateEventType, translateRole, translateWeather } from "../utils/i18n";

const ROLE_ORDER = ["outerwear", "top", "bottom", "shoes", "accessory"];

function getRoleSortIndex(role) {
  const index = ROLE_ORDER.indexOf(String(role || "").toLowerCase());
  return index === -1 ? ROLE_ORDER.length : index;
}

function buildPhotoEntry(outfit) {
  if (!outfit?.styled_photo_url) {
    return null;
  }

  return {
    type: "photo",
    key: `photo-${outfit.id || outfit.name || "outfit"}`,
    imageUrl: resolveAssetUrl(outfit.styled_photo_url),
    title: "Вы в образе",
  };
}

function renderBoardCard(entry, slotName) {
  if (!entry) {
    return null;
  }

  if (entry.type === "photo") {
    return (
      <div key={entry.key} className="board-card board-card-photo">
        <img
          src={entry.imageUrl}
          alt={entry.title}
          className="board-card-image"
          onError={(event) => {
            event.currentTarget.style.display = "none";
          }}
        />
        <div className="board-card-caption">
          <span>Фото</span>
          <strong>{entry.title}</strong>
        </div>
      </div>
    );
  }

  const clothingItem = entry?.clothing_item || entry || {};
  const itemId = entry?.clothing_item_id || clothingItem.id;
  const itemRole = entry?.role || clothingItem.category || slotName;

  return (
    <Link
      key={`${slotName}-${itemId || clothingItem.title || "item"}`}
      to={itemId ? `/wardrobe/${itemId}` : "/wardrobe"}
      className="board-card"
    >
      <img
        src={resolveItemImageUrl(clothingItem, itemRole)}
        alt={clothingItem.title || itemRole}
        className="board-card-image"
        onError={(event) => {
          event.currentTarget.src = getCategoryPlaceholderUrl(
            clothingItem.category || itemRole,
          );
        }}
      />
      <div className="board-card-caption">
        <span>{translateRole(itemRole)}</span>
        <strong>{clothingItem.title || "Вещь"}</strong>
      </div>
    </Link>
  );
}

export default function OutfitCard({
  outfit,
  onSave,
  isSaved,
  onPhotoUpload,
  isUploadingPhoto,
  boardBadge,
  onPrevious,
  onNext,
  onClose,
}) {
  const uploadInputRef = useRef(null);

  const roleMap = useMemo(() => {
    const sortedItems = [...(outfit.items || [])].sort((leftEntry, rightEntry) => {
      const leftRole = leftEntry.role || leftEntry.clothing_item?.category;
      const rightRole = rightEntry.role || rightEntry.clothing_item?.category;
      return getRoleSortIndex(leftRole) - getRoleSortIndex(rightRole);
    });

    return sortedItems.reduce((accumulator, entry) => {
      const role = entry.role || entry.clothing_item?.category || "item";
      if (!accumulator[role]) {
        accumulator[role] = entry;
      }
      return accumulator;
    }, {});
  }, [outfit.items]);

  const boardEntries = useMemo(() => {
    const photoEntry = buildPhotoEntry(outfit);

    return [
      roleMap.outerwear ? { key: "outerwear", slotName: "outerwear", entry: roleMap.outerwear } : null,
      roleMap.top ? { key: "top", slotName: "top", entry: roleMap.top } : null,
      roleMap.accessory ? { key: "accessory", slotName: "accessory", entry: roleMap.accessory } : null,
      roleMap.bottom ? { key: "bottom", slotName: "bottom", entry: roleMap.bottom } : null,
      roleMap.shoes ? { key: "shoes", slotName: "shoes", entry: roleMap.shoes } : null,
      photoEntry ? { key: "photo", slotName: "photo", entry: photoEntry } : null,
    ].filter(Boolean);
  }, [outfit, roleMap]);

  const boardRows = useMemo(() => {
    if (boardEntries.length <= 3) {
      return [boardEntries];
    }

    if (boardEntries.length === 4) {
      return [boardEntries.slice(0, 2), boardEntries.slice(2)];
    }

    return [boardEntries.slice(0, 3), boardEntries.slice(3)];
  }, [boardEntries]);

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
      onClose?.();
    }
  }

  function handlePhotoButtonClick() {
    uploadInputRef.current?.click();
  }

  function handlePhotoChange(event) {
    const file = event.target.files?.[0];
    if (!file || !onPhotoUpload || !outfit.id) {
      return;
    }

    onPhotoUpload(outfit.id, file);
    event.target.value = "";
  }

  return (
    <div className="outfit-modal-backdrop" onClick={handleBackdropClick}>
      <article className="outfit-modal-window">
        <div className="outfit-modal-top-actions">
          <button
            type="button"
            className={`favorite-button ${isSaved ? "is-active" : ""}`}
            onClick={() => onSave?.(outfit)}
            disabled={!onSave || isSaved}
            aria-label={isSaved ? "Образ уже в избранном" : "Сохранить образ в избранное"}
            title={isSaved ? "Уже в избранном" : "Сохранить в избранное"}
          >
            {isSaved ? "♥" : "♡"}
          </button>
          <button
            type="button"
            className="modal-close-button"
            onClick={onClose}
            aria-label="Закрыть просмотр"
          >
            ×
          </button>
        </div>

        <div className="outfit-modal-bottom-actions">
          <button
            type="button"
            className="arrow-button"
            onClick={onPrevious}
            aria-label="Предыдущий образ"
          >
            ←
          </button>
          <button
            type="button"
            className="arrow-button"
            onClick={onNext}
            aria-label="Следующий образ"
          >
            →
          </button>
        </div>

        <div className="outfit-modal-content">
          <section className="outfit-modal-left">
            <div className="outfit-board-canvas">
              {boardBadge ? (
                <div className="board-meta-strip">
                  <div className="board-index-chip">{boardBadge}</div>
                </div>
              ) : null}

              <div className={`board-grid board-grid-count-${boardEntries.length || 0}`}>
                {boardRows.map((row, rowIndex) => (
                  <div
                    key={`row-${rowIndex}`}
                    className={`board-row board-row-${row.length} ${
                      rowIndex === 0 ? "board-row-top" : "board-row-bottom"
                    }`}
                  >
                    {row.map(({ key, slotName, entry }) => (
                      <div
                        key={key}
                        className={`board-slot board-slot-${slotName} board-slot-active`}
                      >
                        {renderBoardCard(entry, slotName)}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </section>

          <aside className="outfit-modal-sidebar">
            <div className="outfit-side-copy">
              <p className="eyebrow">Разбор образа</p>
              <h2>{outfit.name || "Собранный образ"}</h2>
              <p className="outfit-board-context">
                {translateEventType(outfit.event_type) || "Образ"}
                {outfit.weather_context?.temperature !== undefined &&
                outfit.weather_context?.temperature !== null
                  ? ` • ${outfit.weather_context.temperature}°C`
                  : ""}
                {outfit.weather_context?.weather_condition
                  ? ` • ${translateWeather(outfit.weather_context.weather_condition)}`
                  : ""}
              </p>
            </div>

            <div className="outfit-summary-card">
              <div className="score-ring">
                <strong>{Number(outfit.score || 0).toFixed(2)}</strong>
                <span>Итоговая оценка</span>
              </div>

              <p className="outfit-summary-text">{outfit.explanation}</p>
            </div>

            <div className="outfit-comments-list">
              {(outfit.reasons || []).map((reason) => (
                <div key={reason} className="outfit-comment-pill">
                  {reason}
                </div>
              ))}
            </div>

            {outfit.id && onPhotoUpload ? (
              <div className="outfit-photo-actions">
                <input
                  ref={uploadInputRef}
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={handlePhotoChange}
                />
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handlePhotoButtonClick}
                  disabled={isUploadingPhoto}
                >
                  {isUploadingPhoto
                    ? "Загрузка фото..."
                    : outfit.styled_photo_url
                      ? "Обновить фото в образе"
                      : "Добавить своё фото к образу"}
                </button>
                <p className="muted-text">
                  После сохранения можно добавить фото себя в этом образе.
                </p>
              </div>
            ) : null}
          </aside>
        </div>
      </article>
    </div>
  );
}
