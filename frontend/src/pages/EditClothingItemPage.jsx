import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { fetchItemById, updateItem } from "../api/itemsApi";
import ClothingItemForm from "../components/ClothingItemForm";
import useAuth from "../hooks/useAuth";


export default function EditClothingItemPage() {
  const { itemId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
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

  async function handleSubmit(formData) {
    setSaving(true);
    setError("");

    try {
      await updateItem(token, itemId, formData);
      navigate("/wardrobe");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <section className="page-section">
        <div className="card">Загрузка вещи...</div>
      </section>
    );
  }

  return (
    <section className="page-section">
      {error ? <p className="error-text">{error}</p> : null}
      <ClothingItemForm
        initialValues={item}
        submitLabel="Обновить вещь"
        onSubmit={handleSubmit}
        loading={saving}
      />
    </section>
  );
}
