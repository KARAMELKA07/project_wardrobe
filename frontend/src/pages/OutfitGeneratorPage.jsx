import { useEffect, useMemo, useRef, useState } from "react";

import { fetchItems } from "../api/itemsApi";
import { generateOutfits, saveOutfit, uploadOutfitPhoto } from "../api/outfitsApi";
import OutfitCard from "../components/OutfitCard";
import useAuth from "../hooks/useAuth";
import useCurrentWeather from "../hooks/useCurrentWeather";
import { translateCategory } from "../utils/i18n";
import { resolveWeatherLocation } from "../utils/weatherLocation";


const INITIAL_FORM = {
  event_type: "office",
  preferred_colors: "",
  preferred_style: "",
  temperature: "",
  weather_condition: "",
  anchor_item_id: "",
  constraints: "",
};


export default function OutfitGeneratorPage() {
  const { token, user } = useAuth();
  const { weather } = useCurrentWeather(token, user?.city);
  const weatherPrefilledRef = useRef(false);

  const [items, setItems] = useState([]);
  const [formValues, setFormValues] = useState(INITIAL_FORM);
  const [generatedOutfits, setGeneratedOutfits] = useState([]);
  const [savedKeys, setSavedKeys] = useState({});
  const [hasGenerated, setHasGenerated] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [resultMessage, setResultMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [error, setError] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    async function loadItems() {
      try {
        const response = await fetchItems(token);
        setItems(response.items || []);
      } catch (requestError) {
        setError(requestError.message);
      }
    }

    loadItems();
  }, [token]);

  useEffect(() => {
    if (weatherPrefilledRef.current || !weather) {
      return;
    }

    setFormValues((currentValues) => ({
      ...currentValues,
      temperature:
        currentValues.temperature === "" && weather.temperature !== null && weather.temperature !== undefined
          ? String(weather.temperature)
          : currentValues.temperature,
      weather_condition:
        !currentValues.weather_condition && weather.weather_condition
          ? weather.weather_condition
          : currentValues.weather_condition,
    }));
    weatherPrefilledRef.current = true;
  }, [weather]);

  const activeOutfit = useMemo(() => {
    if (!generatedOutfits.length) {
      return null;
    }

    return generatedOutfits[activeIndex] || generatedOutfits[0];
  }, [activeIndex, generatedOutfits]);

  function handleChange(event) {
    const { name, value } = event.target;
    setFormValues((currentValues) => ({ ...currentValues, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResultMessage("");

    try {
      const shouldResolveWeatherAutomatically =
        !formValues.temperature || !formValues.weather_condition;
      const location = shouldResolveWeatherAutomatically
        ? await resolveWeatherLocation({ allowPrompt: true })
        : null;

      const payload = {
        ...formValues,
        anchor_item_id: formValues.anchor_item_id || null,
        temperature: formValues.temperature || null,
        latitude: location?.latitude ?? null,
        longitude: location?.longitude ?? null,
      };

      const response = await generateOutfits(token, payload);
      setGeneratedOutfits(response.outfits || []);
      setSavedKeys({});
      setHasGenerated(true);
      setResultMessage(response.message || "");
      setActiveIndex(0);
      setIsModalOpen(Boolean(response.outfits?.length));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave(outfit) {
    setError("");

    try {
      const response = await saveOutfit(token, {
        name: outfit.name,
        event_type: outfit.event_type,
        weather_context: outfit.weather_context,
        score: outfit.score,
        explanation: outfit.explanation,
        feature_scores: outfit.feature_scores || {},
        reasons: outfit.reasons || [],
        items: outfit.items.map((entry) => ({
          clothing_item_id: entry.clothing_item_id || entry.id,
          role: entry.role,
        })),
      });

      const savedOutfit = response.outfit;
      setGeneratedOutfits((currentOutfits) =>
        currentOutfits.map((entry, index) => (index === activeIndex ? savedOutfit : entry)),
      );
      setSavedKeys((currentKeys) => ({
        ...currentKeys,
        [savedOutfit.id || savedOutfit.name]: true,
      }));
      setResultMessage("Образ сохранен. Теперь можно добавить фото.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function handlePhotoUpload(outfitId, file) {
    setUploadingPhoto(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("image", file);
      const response = await uploadOutfitPhoto(token, outfitId, formData);
      const updatedOutfit = response.outfit;

      setGeneratedOutfits((currentOutfits) =>
        currentOutfits.map((entry) => (entry.id === outfitId ? updatedOutfit : entry)),
      );
      setResultMessage("Фото добавлено. Карточка образа обновлена.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setUploadingPhoto(false);
    }
  }

  function showPreviousOutfit() {
    setActiveIndex((currentIndex) =>
      currentIndex === 0 ? generatedOutfits.length - 1 : currentIndex - 1,
    );
  }

  function showNextOutfit() {
    setActiveIndex((currentIndex) =>
      currentIndex === generatedOutfits.length - 1 ? 0 : currentIndex + 1,
    );
  }

  return (
    <section className="page-section generator-page">
      <div className="section-heading section-heading-stack">
        <div>
          <h1>Соберите подборку образов</h1>
        </div>
      </div>

      <form className="surface-card form-card generator-form-card" onSubmit={handleSubmit}>
        <div className="form-grid">
          <label>
            Тип события
            <select
              className="input"
              name="event_type"
              value={formValues.event_type}
              onChange={handleChange}
            >
              <option value="office">Офис</option>
              <option value="casual">Повседневный</option>
              <option value="evening">Вечерний</option>
              <option value="sport">Спортивный</option>
              <option value="party">Вечеринка</option>
              <option value="travel">Поездка</option>
              <option value="date">Свидание</option>
            </select>
          </label>

          <label>
            Предпочтительные цвета
            <input
              className="input"
              name="preferred_colors"
              value={formValues.preferred_colors}
              onChange={handleChange}
            />
          </label>

          <label>
            Предпочтительный стиль
            <input
              className="input"
              name="preferred_style"
              value={formValues.preferred_style}
              onChange={handleChange}
            />
          </label>

          <label>
            Опорная вещь
            <select
              className="input"
              name="anchor_item_id"
              value={formValues.anchor_item_id}
              onChange={handleChange}
            >
              <option value="">Без опорной вещи</option>
              {items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.title} ({translateCategory(item.category)})
                </option>
              ))}
            </select>
          </label>

          <label>
            Погода
            <select
              className="input"
              name="weather_condition"
              value={formValues.weather_condition}
              onChange={handleChange}
            >
              <option value="">Определить автоматически</option>
              <option value="sunny">Солнечно</option>
              <option value="cloudy">Облачно</option>
              <option value="clear">Ясно</option>
              <option value="rain">Дождь</option>
              <option value="snow">Снег</option>
              <option value="wind">Ветрено</option>
            </select>
          </label>

          <label>
            Температура
            <input
              className="input"
              name="temperature"
              type="number"
              value={formValues.temperature}
              onChange={handleChange}
            />
          </label>

          <label className="full-width">
            Ограничения
            <input
              className="input"
              name="constraints"
              value={formValues.constraints}
              onChange={handleChange}
            />
          </label>
        </div>

        <button type="submit" className="primary-button primary-button-wide" disabled={loading}>
          {loading ? "Подбор..." : "Создать образы"}
        </button>
      </form>

      {error ? <p className="error-text">{error}</p> : null}
      {resultMessage ? <p className="muted-text">{resultMessage}</p> : null}

      {!loading && hasGenerated && generatedOutfits.length === 0 ? (
        <div className="surface-card empty-state">
          {resultMessage || "Для выбранных параметров не найдено подходящих сочетаний."}
        </div>
      ) : null}

      {isModalOpen && activeOutfit ? (
        <OutfitCard
          outfit={activeOutfit}
          onSave={handleSave}
          isSaved={Boolean(savedKeys[activeOutfit.id || activeOutfit.name])}
          onPhotoUpload={handlePhotoUpload}
          isUploadingPhoto={uploadingPhoto}
          boardBadge={`${activeIndex + 1}/${generatedOutfits.length}`}
          onPrevious={showPreviousOutfit}
          onNext={showNextOutfit}
          onClose={() => setIsModalOpen(false)}
        />
      ) : null}
    </section>
  );
}
