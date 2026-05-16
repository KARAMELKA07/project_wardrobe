import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { deleteItem, fetchItemById } from "../api/itemsApi";
import useAuth from "../hooks/useAuth";
import { CloseIcon } from "../icons/AppIcons";
import ClothingItemDetailsCard from "./ClothingItemDetailsCard";

export default function ClothingItemDetailsModal() {
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

  useEffect(() => {
    document.body.classList.add("item-detail-modal-active");

    return () => {
      document.body.classList.remove("item-detail-modal-active");
    };
  }, []);

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
      navigate(-1);
    } catch (requestError) {
      setError(requestError.message);
      setDeleting(false);
    }
  }

  function handleClose() {
    navigate(-1);
  }

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
      handleClose();
    }
  }

  return (
    <div className="item-detail-backdrop" onClick={handleBackdropClick}>
      <div className="item-detail-modal-window">
        <button
          type="button"
          className="circle-action-button item-detail-close"
          onClick={handleClose}
          aria-label="Закрыть карточку вещи"
        >
          <CloseIcon />
        </button>

        {loading ? <div className="surface-card">Загрузка карточки вещи...</div> : null}
        {!loading && error && !item ? <div className="surface-card error-text">{error}</div> : null}

        {item ? (
          <>
            {error ? <p className="error-text">{error}</p> : null}
            <ClothingItemDetailsCard
              item={item}
              deleting={deleting}
              onDelete={handleDelete}
            />
          </>
        ) : null}
      </div>
    </div>
  );
}
