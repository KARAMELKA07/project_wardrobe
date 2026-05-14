import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { deleteItem, fetchItemById } from "../api/itemsApi";
import ClothingItemDetailsCard from "../components/ClothingItemDetailsCard";
import useAuth from "../hooks/useAuth";

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

      <ClothingItemDetailsCard
        item={item}
        deleting={deleting}
        onDelete={handleDelete}
      />
    </section>
  );
}
