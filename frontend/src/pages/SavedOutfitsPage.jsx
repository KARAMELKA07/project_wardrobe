import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { fetchSavedOutfits, uploadOutfitPhoto } from "../api/outfitsApi";
import OutfitCard from "../components/OutfitCard";
import useAuth from "../hooks/useAuth";

export default function SavedOutfitsPage() {
  const { token } = useAuth();
  const [outfits, setOutfits] = useState([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    async function loadSavedOutfits() {
      setLoading(true);
      setError("");

      try {
        const response = await fetchSavedOutfits(token);
        setOutfits(response.outfits || []);
        setActiveIndex(0);
        setIsModalOpen(Boolean(response.outfits?.length));
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    }

    loadSavedOutfits();
  }, [token]);

  const activeOutfit = useMemo(() => {
    if (!outfits.length) {
      return null;
    }

    return outfits[activeIndex] || outfits[0];
  }, [activeIndex, outfits]);

  async function handlePhotoUpload(outfitId, file) {
    setUploadingPhoto(true);
    setError("");
    setMessage("");

    try {
      const formData = new FormData();
      formData.append("image", file);
      const response = await uploadOutfitPhoto(token, outfitId, formData);
      const updatedOutfit = response.outfit;

      setOutfits((currentOutfits) =>
        currentOutfits.map((entry) =>
          entry.id === outfitId ? updatedOutfit : entry,
        ),
      );
      setMessage("Фото добавлено. Доска образа обновлена.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setUploadingPhoto(false);
    }
  }

  function showPreviousOutfit() {
    setActiveIndex((currentIndex) =>
      currentIndex === 0 ? outfits.length - 1 : currentIndex - 1,
    );
  }

  function showNextOutfit() {
    setActiveIndex((currentIndex) =>
      currentIndex === outfits.length - 1 ? 0 : currentIndex + 1,
    );
  }

  return (
    <section className="page-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Избранное</p>
          <h1>Сохранённые образы</h1>
          <p className="muted-text">
            Все сохранённые образы открываются как отдельные доски во всплывающем окне.
          </p>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      {message ? <p className="muted-text">{message}</p> : null}

      {loading ? (
        <div className="card empty-state">Загружаем сохранённые образы...</div>
      ) : null}

      {!loading && !activeOutfit ? (
        <div className="card empty-state">
          <h3>Пока нет сохранённых образов</h3>
          <p className="muted-text">
            Сначала сгенерируйте образы и нажмите на сердечко, чтобы сохранить лучший вариант.
          </p>
          <Link to="/generate" className="primary-button">
            Перейти к подбору образов
          </Link>
        </div>
      ) : null}

      {!loading && activeOutfit && !isModalOpen ? (
        <div className="card centered-card">
          <h3>Сохранённые доски готовы</h3>
          <p className="muted-text">
            Откройте модальное окно, чтобы пролистать сохранённые образы.
          </p>
          <button
            type="button"
            className="primary-button"
            onClick={() => setIsModalOpen(true)}
          >
            Открыть сохранённые доски
          </button>
        </div>
      ) : null}

      {isModalOpen && activeOutfit ? (
        <OutfitCard
          outfit={activeOutfit}
          isSaved
          onPhotoUpload={handlePhotoUpload}
          isUploadingPhoto={uploadingPhoto}
          boardBadge={`${activeIndex + 1}/${outfits.length}`}
          onPrevious={showPreviousOutfit}
          onNext={showNextOutfit}
          onClose={() => setIsModalOpen(false)}
        />
      ) : null}
    </section>
  );
}
