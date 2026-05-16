import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import {
    getCategoryPlaceholderUrl,
    resolveAssetUrl,
    resolveItemImageUrl,
} from "../api/client";
import {
    ArrowLeftIcon,
    ArrowRightIcon,
    CloseIcon,
    FlipIcon,
    HeartIcon,
    TrashIcon,
} from "../icons/AppIcons";
import { translateEventType, translateRole, translateWeather } from "../utils/i18n";

const ROLE_ORDER = ["outerwear", "dress", "top", "bottom", "shoes", "accessory"];
const KNOWN_BOARD_ROLES = new Set(ROLE_ORDER);

function getRoleSortIndex(role) {
    const index = ROLE_ORDER.indexOf(String(role || "").toLowerCase());
    return index === -1 ? ROLE_ORDER.length : index;
}

function getEntryRole(entry, fallbackRole = "item") {
    const clothingItem = entry?.clothing_item || entry || {};
    return String(entry?.role || clothingItem.category || fallbackRole || "item").toLowerCase();
}

function getSlotName(role) {
    return KNOWN_BOARD_ROLES.has(role) ? role : "item";
}

function getItemKey(entry, role, index) {
    const clothingItem = entry?.clothing_item || entry || {};
    const itemId = entry?.clothing_item_id || clothingItem.id || entry?.id;
    return `${role}-${itemId || clothingItem.title || index}`;
}

function renderBoardCard(entry, slotName, linkState) {
    if (!entry) {
        return null;
    }

    const clothingItem = entry?.clothing_item || entry || {};
    const itemId = entry?.clothing_item_id || clothingItem.id;
    const itemRole = entry?.role || clothingItem.category || slotName;

    return (
        <Link
            key={`${slotName}-${itemId || clothingItem.title || "item"}`}
            to={itemId ? `/wardrobe/${itemId}` : "/wardrobe"}
            state={itemId ? linkState : undefined}
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
    onDelete,
    onPhotoUpload,
    isUploadingPhoto,
    isDeleting,
    boardBadge,
    onPrevious,
    onNext,
    onClose,
}) {
    const uploadInputRef = useRef(null);
    const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
    const [isPhotoInfoOpen, setIsPhotoInfoOpen] = useState(false);
    const location = useLocation();
    const canUploadPhoto = Boolean(isSaved && outfit?.id && onPhotoUpload);
    const styledPhotoUrl = outfit?.styled_photo_url
        ? resolveAssetUrl(outfit.styled_photo_url)
        : null;
    const scoreValue = Number(outfit.score || 0).toFixed(2);

    useEffect(() => {
        setIsDeleteConfirmOpen(false);
        setIsPhotoInfoOpen(false);
    }, [outfit?.id, styledPhotoUrl]);

    const itemEntries = useMemo(() => {
        const roleCounts = {};
        let extraSlotIndex = 0;

        return [...(outfit.items || [])]
            .map((entry, index) => ({
                entry,
                index,
                role: getEntryRole(entry),
            }))
            .sort((leftEntry, rightEntry) => {
                const roleDiff =
                    getRoleSortIndex(leftEntry.role) - getRoleSortIndex(rightEntry.role);
                return roleDiff || leftEntry.index - rightEntry.index;
            })
            .map(({ entry, index, role }) => {
                const slotName = getSlotName(role);
                roleCounts[slotName] = (roleCounts[slotName] || 0) + 1;
                const occurrence = roleCounts[slotName];
                const isExtra = occurrence > 1 || slotName === "item";
                const currentExtraSlotIndex = isExtra ? extraSlotIndex : null;
                if (isExtra) {
                    extraSlotIndex += 1;
                }

                return {
                    key: getItemKey(entry, role, index),
                    slotName,
                    role,
                    occurrence,
                    isExtra,
                    extraSlotIndex: currentExtraSlotIndex,
                    entry,
                };
            });
    }, [outfit.items]);

    const boardEntries = itemEntries;
    const hasDress = itemEntries.some((entry) => entry.slotName === "dress");

    const reasons = useMemo(
        () => (outfit.reasons || []).filter(Boolean).slice(0, 4),
        [outfit.reasons],
    );

    const contextParts = [
        translateEventType(outfit.event_type) || "Образ",
        outfit.weather_context?.temperature !== undefined &&
            outfit.weather_context?.temperature !== null
            ? `${outfit.weather_context.temperature}°C`
            : null,
        outfit.weather_context?.weather_condition
            ? translateWeather(outfit.weather_context.weather_condition)
            : null,
    ].filter(Boolean);

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

    async function handleConfirmDelete() {
        if (!onDelete || !outfit?.id) {
            return;
        }

        await onDelete(outfit);
        setIsDeleteConfirmOpen(false);
    }

    function renderScoreRing(className = "") {
        return (
            <div className={["score-ring", className].filter(Boolean).join(" ")}>
                <strong>{scoreValue}</strong>
                <span>Итоговая оценка</span>
            </div>
        );
    }

    function renderSummaryBlock() {
        return (
            <>
                <div className="outfit-summary-card">
                    {renderScoreRing()}
                    <p className="outfit-summary-text">{outfit.explanation}</p>
                </div>

                {reasons.length ? (
                    <div className="outfit-comments-list">
                        {reasons.map((reason) => (
                            <div key={reason} className="outfit-comment-pill">
                                {reason}
                            </div>
                        ))}
                    </div>
                ) : null}
            </>
        );
    }

    return (
        <div className="outfit-modal-backdrop" onClick={handleBackdropClick}>
            <article className="outfit-modal-window">
                <div className="outfit-modal-content">
                    <section className="outfit-modal-left">
                        <div className="outfit-board-canvas">
                            {boardBadge ? (
                                <div className="board-meta-strip">
                                    <div className="board-index-chip">{boardBadge}</div>
                                </div>
                            ) : null}

                            <div
                                className={[
                                    "board-grid",
                                    `board-grid-count-${boardEntries.length || 0}`,
                                    `board-grid-items-${itemEntries.length || 0}`,
                                    hasDress ? "board-grid-has-dress" : "",
                                ]
                                    .filter(Boolean)
                                    .join(" ")}
                            >
                                {boardEntries.map(
                                    ({ key, slotName, entry, isExtra, extraSlotIndex, occurrence }, index) => (
                                        <div
                                            key={key}
                                            className={[
                                                "board-slot",
                                                `board-slot-${slotName}`,
                                                `board-slot-index-${index}`,
                                                occurrence > 1 ? `board-slot-occurrence-${occurrence}` : "",
                                                isExtra ? "board-slot-extra" : "",
                                                isExtra ? `board-slot-extra-${extraSlotIndex % 4}` : "",
                                            ]
                                                .filter(Boolean)
                                                .join(" ")}
                                        >
                                            {renderBoardCard(entry, slotName, { backgroundLocation: location })}
                                        </div>
                                    ),
                                )}
                            </div>
                        </div>
                    </section>

                    <aside className="outfit-modal-sidebar">
                        <div className="outfit-modal-sidebar-head">
                            <div className="outfit-side-copy">
                                <h2>{outfit.name || "Образ"}</h2>
                                <p className="outfit-board-context">{contextParts.join(" · ")}</p>
                            </div>

                            <div className="outfit-modal-top-actions">
                                {isSaved ? (
                                    <button
                                        type="button"
                                        className="circle-action-button is-danger"
                                        onClick={() => setIsDeleteConfirmOpen(true)}
                                        disabled={!onDelete || isDeleting}
                                        aria-label="Удалить образ из сохранённых"
                                        title="Удалить из сохранённых"
                                    >
                                        <TrashIcon />
                                    </button>
                                ) : (
                                    <button
                                        type="button"
                                        className="circle-action-button"
                                        onClick={() => onSave?.(outfit)}
                                        disabled={!onSave}
                                        aria-label="Сохранить образ"
                                        title="Сохранить"
                                    >
                                        <HeartIcon />
                                    </button>
                                )}
                                <button
                                    type="button"
                                    className="circle-action-button"
                                    onClick={onClose}
                                    aria-label="Закрыть просмотр"
                                >
                                    <CloseIcon />
                                </button>
                            </div>
                        </div>

                        {styledPhotoUrl ? (
                            <div
                                className={[
                                    "outfit-photo-flip-card",
                                    isPhotoInfoOpen ? "is-flipped" : "",
                                ]
                                    .filter(Boolean)
                                    .join(" ")}
                            >
                                <div className="outfit-photo-flip-inner">
                                    <div className="outfit-photo-flip-face outfit-photo-front">
                                        <div className="outfit-styled-photo-card">
                                            <img
                                                src={styledPhotoUrl}
                                                alt="Вы в образе"
                                                className="outfit-styled-photo-image"
                                                onError={(event) => {
                                                    event.currentTarget.style.display = "none";
                                                }}
                                            />

                                            {renderScoreRing("outfit-photo-score-ring")}

                                            <button
                                                type="button"
                                                className="outfit-photo-info-button"
                                                onClick={() => setIsPhotoInfoOpen(true)}
                                                aria-label="Показать описание образа"
                                                title="Показать описание образа"
                                            >
                                                <FlipIcon />
                                            </button>
                                        </div>
                                    </div>

                                    <div className="outfit-photo-flip-face outfit-photo-back">
                                        <div className="outfit-photo-back-panel">
                                            <button
                                                type="button"
                                                className="outfit-photo-info-button outfit-photo-back-button"
                                                onClick={() => setIsPhotoInfoOpen(false)}
                                                aria-label="Вернуться к фото"
                                                title="Вернуться к фото"
                                            >
                                                <FlipIcon />
                                            </button>

                                            <div className="outfit-photo-back-content">
                                                {renderSummaryBlock()}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="outfit-info-panel">
                                {renderSummaryBlock()}
                            </div>
                        )}

                        <div className="outfit-modal-sidebar-spacer" />

                        <div className="outfit-photo-actions">
                            {canUploadPhoto ? (
                                <>
                                    <input
                                        ref={uploadInputRef}
                                        type="file"
                                        accept="image/*"
                                        hidden
                                        onChange={handlePhotoChange}
                                    />
                                    <button
                                        type="button"
                                        className="secondary-button outfit-photo-button"
                                        onClick={handlePhotoButtonClick}
                                        disabled={isUploadingPhoto}
                                    >
                                        {isUploadingPhoto
                                            ? "Загрузка фото..."
                                            : outfit.styled_photo_url
                                                ? "Обновить фото в образе"
                                                : "Добавить фото в образ"}
                                    </button>
                                </>
                            ) : null}

                            <div className="outfit-modal-bottom-actions">
                                <button
                                    type="button"
                                    className="circle-action-button"
                                    onClick={onPrevious}
                                    aria-label="Предыдущий образ"
                                >
                                    <ArrowLeftIcon />
                                </button>
                                <button
                                    type="button"
                                    className="circle-action-button"
                                    onClick={onNext}
                                    aria-label="Следующий образ"
                                >
                                    <ArrowRightIcon />
                                </button>
                            </div>
                        </div>
                    </aside>
                </div>

                {isDeleteConfirmOpen ? (
                    <div className="outfit-delete-confirm" role="dialog" aria-modal="true">
                        <div className="outfit-delete-confirm-card">
                            <h3>Удалить образ?</h3>
                            <p>Он исчезнет из сохранённых образов.</p>

                            <div className="outfit-delete-confirm-actions">
                                <button
                                    type="button"
                                    className="secondary-button"
                                    onClick={() => setIsDeleteConfirmOpen(false)}
                                    disabled={isDeleting}
                                >
                                    Нет
                                </button>
                                <button
                                    type="button"
                                    className="primary-button danger-button"
                                    onClick={handleConfirmDelete}
                                    disabled={isDeleting}
                                >
                                    {isDeleting ? "Удаление..." : "Да, удалить"}
                                </button>
                            </div>
                        </div>
                    </div>
                ) : null}
            </article>
        </div>
    );
}
