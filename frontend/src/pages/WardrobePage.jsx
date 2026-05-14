import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { deleteItem, fetchItems } from "../api/itemsApi";
import { getCategoryPlaceholderUrl, resolveItemImageUrl } from "../api/client";
import { PencilIcon, TrashIcon } from "../icons/AppIcons";
import useAuth from "../hooks/useAuth";


export default function WardrobePage() {
  const navigate = useNavigate();
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

  const bannerText = useMemo(() => {
    if (!items.length) {
      return "Добавьте первые вещи, чтобы собрать цифровой гардероб.";
    }

    return "Состав гардероба выглядит достаточно сбалансированным";
  }, [items]);

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

  function handleOpenItem(itemId) {
    navigate(`/wardrobe/${itemId}`);
  }

  function handleCardKeyDown(event, itemId) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      handleOpenItem(itemId);
    }
  }

  return (
    <section className="page-section wardrobe-page">
      <div className="section-heading section-heading-stack">
        <div>
          <h1>Ваши вещи</h1>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      <section className="overview-banner">
        <div className="overview-banner-copy">
          <p>{bannerText}</p>
        </div>
        <div className="overview-banner-accent" />
      </section>

      {loading ? <div className="surface-card">Загрузка гардероба...</div> : null}

      {!loading && items.length === 0 ? (
        <div className="surface-card empty-state">
          Пока вещей нет. Добавьте верх, низ, обувь и аксессуары, чтобы начать подбор образов.
        </div>
      ) : null}

      <div className="wardrobe-grid">
        {items.map((item) => (
          <article
            key={item.id}
            className="wardrobe-card"
            role="button"
            tabIndex={0}
            onClick={() => handleOpenItem(item.id)}
            onKeyDown={(event) => handleCardKeyDown(event, item.id)}
          >
            <img
              src={resolveItemImageUrl(item)}
              alt={item.title}
              className="wardrobe-card-image"
              onError={(event) => {
                event.currentTarget.src = getCategoryPlaceholderUrl(item.category);
              }}
            />

            <div className="wardrobe-card-footer">
              <span className="wardrobe-card-title">{item.title}</span>

              <div className="wardrobe-card-actions">
                <Link
                  to={`/wardrobe/${item.id}/edit`}
                  className="icon-button"
                  aria-label="Редактировать вещь"
                  title="Редактировать"
                  onClick={(event) => event.stopPropagation()}
                >
                  <PencilIcon />
                </Link>
                <button
                  type="button"
                  className="icon-button"
                  aria-label="Удалить вещь"
                  title="Удалить"
                  onClick={(event) => {
                    event.stopPropagation();
                    handleDelete(item.id);
                  }}
                >
                  <TrashIcon />
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
