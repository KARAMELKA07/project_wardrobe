import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { createItem } from "../api/itemsApi";
import ClothingItemForm from "../components/ClothingItemForm";
import useAuth from "../hooks/useAuth";


export default function AddClothingItemPage() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(formData) {
    setLoading(true);
    setError("");

    try {
      await createItem(token, formData);
      navigate("/wardrobe");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page-section">
      {error ? <p className="error-text">{error}</p> : null}
      <ClothingItemForm
        submitLabel="Создать вещь"
        onSubmit={handleSubmit}
        loading={loading}
      />
    </section>
  );
}
