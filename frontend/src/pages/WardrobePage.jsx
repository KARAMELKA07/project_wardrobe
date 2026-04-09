import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { deleteItem, fetchItems } from "../api/itemsApi";
import {
  getCategoryPlaceholderUrl,
  resolveItemImageUrl,
} from "../api/client";
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
          <article
            key={item.id}
            className="card item-card item-card-compact item-card-clickable"
            role="button"
            tabIndex={0}
            onClick={() => handleOpenItem(item.id)}
            onKeyDown={(event) => handleCardKeyDown(event, item.id)}
          >
            <img
              src={resolveItemImageUrl(item)}
              alt={item.title}
              className="item-cover"
              onError={(event) => {
                event.currentTarget.src = getCategoryPlaceholderUrl(item.category);
              }}
            />

            <div className="item-body">
              <div className="item-compact-footer">
                <h3 className="item-compact-title">{item.title}</h3>
                <div className="item-icon-actions">
                  <Link
                    to={`/wardrobe/${item.id}/edit`}
                    className="item-icon-button"
                    aria-label="Редактировать вещь"
                    title="Редактировать"
                    onClick={(event) => event.stopPropagation()}
                  >
                    ✎
                  </Link>
                  <button
                    type="button"
                    className="item-icon-button item-icon-button-danger"
                    aria-label="Удалить вещь"
                    title="Удалить"
                    onClick={(event) => {
                      event.stopPropagation();
                      handleDelete(item.id);
                    }}
                  >
                    🗑
                  </button>
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
