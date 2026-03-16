import { useEffect, useState } from "react";

import { fetchSavedOutfits, sendOutfitFeedback } from "../api/outfitsApi";
import OutfitCard from "../components/OutfitCard";
import useAuth from "../hooks/useAuth";


export default function SavedOutfitsPage() {
  const { token } = useAuth();
  const [outfits, setOutfits] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadOutfits() {
      try {
        const response = await fetchSavedOutfits(token);
        setOutfits(response.outfits);
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    }

    loadOutfits();
  }, [token]);

  async function handleReaction(outfitId, reaction) {
    try {
      await sendOutfitFeedback(token, outfitId, reaction);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <section className="page-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Образы</p>
          <h1>Сохраненные комбинации</h1>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      {loading ? <div className="card">Загрузка сохраненных образов...</div> : null}

      {!loading && outfits.length === 0 ? (
        <div className="card empty-state">
          Пока нет сохраненных образов. Сгенерируйте варианты и сохраните лучшие.
        </div>
      ) : null}

      <div className="outfit-grid">
        {outfits.map((outfit) => (
          <OutfitCard key={outfit.id} outfit={outfit} onReact={handleReaction} />
        ))}
      </div>
    </section>
  );
}
