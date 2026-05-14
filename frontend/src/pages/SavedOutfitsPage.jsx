import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getCategoryPlaceholderUrl, resolveAssetUrl, resolveItemImageUrl } from "../api/client";
import { fetchSavedOutfits, uploadOutfitPhoto } from "../api/outfitsApi";
import OutfitCard from "../components/OutfitCard";
import useAuth from "../hooks/useAuth";


function resolveOutfitPreview(outfit) {
  if (outfit?.styled_photo_url) {
    return resolveAssetUrl(outfit.styled_photo_url);
  }

  const firstItem = outfit?.items?.[0]?.clothing_item || outfit?.items?.[0];
  if (firstItem) {
    return resolveItemImageUrl(firstItem);
  }

  return getCategoryPlaceholderUrl("top");
}


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
        currentOutfits.map((entry) => (entry.id === outfitId ? updatedOutfit : entry)),
      );
      setMessage("Фото добавлено. Карточка образа обновлена.");
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

  function openOutfit(index) {
    setActiveIndex(index);
    setIsModalOpen(true);
  }

  return (
    <section className="page-section saved-outfits-page">
      <div className="section-heading section-heading-stack">
        <div>
          <h1>Сохраненные образы</h1>
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      {message ? <p className="muted-text">{message}</p> : null}

      {loading ? <div className="surface-card empty-state">Загружаем сохраненные образы...</div> : null}

      {!loading && !outfits.length ? (
        <div className="surface-card empty-state">
          <h3>Пока нет сохраненных образов</h3>
          <p className="muted-text">
            Сначала сгенерируйте образы и сохраните понравившийся вариант.
          </p>
          <Link to="/generate" className="primary-button">
            Перейти к подбору образов
          </Link>
        </div>
      ) : null}

      <div className="saved-outfits-grid">
        {outfits.map((outfit, index) => (
          <button
            key={outfit.id || `${outfit.name}-${index}`}
            type="button"
            className="saved-outfit-card"
            onClick={() => openOutfit(index)}
          >
            <img
              src={resolveOutfitPreview(outfit)}
              alt={outfit.name}
              className="saved-outfit-card-image"
            />
            <div className="saved-outfit-card-footer">
              <span>{outfit.name}</span>
              <span className="saved-outfit-card-mark" />
            </div>
          </button>
        ))}
      </div>

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
