import { useEffect, useState } from "react";

import { fetchItems } from "../api/itemsApi";
import { generateOutfits, saveOutfit } from "../api/outfitsApi";
import OutfitCard from "../components/OutfitCard";
import useAuth from "../hooks/useAuth";
import {
  translateCategory,
  translateSeason,
  translateWeather,
} from "../utils/i18n";


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
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const [formValues, setFormValues] = useState(INITIAL_FORM);
  const [generatedOutfits, setGeneratedOutfits] = useState([]);
  const [weather, setWeather] = useState(null);
  const [savedKeys, setSavedKeys] = useState({});
  const [hasGenerated, setHasGenerated] = useState(false);
  const [resultMessage, setResultMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadItems() {
      try {
        const response = await fetchItems(token);
        setItems(response.items);
      } catch (requestError) {
        setError(requestError.message);
      }
    }

    loadItems();
  }, [token]);

  function handleChange(event) {
    const { name, value } = event.target;
    setFormValues((currentValues) => ({ ...currentValues, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload = {
        ...formValues,
        anchor_item_id: formValues.anchor_item_id || null,
        temperature: formValues.temperature || null,
      };
      const response = await generateOutfits(token, payload);
      setGeneratedOutfits(response.outfits);
      setWeather(response.weather);
      setSavedKeys({});
      setHasGenerated(true);
      setResultMessage(response.message || "");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave(outfit) {
    try {
      await saveOutfit(token, {
        name: outfit.name,
        event_type: outfit.event_type,
        weather_context: outfit.weather_context,
        score: outfit.score,
        explanation: outfit.explanation,
        items: outfit.items.map((entry) => ({
          clothing_item_id: entry.clothing_item_id || entry.id,
          role: entry.role,
        })),
      });
      setSavedKeys((currentKeys) => ({ ...currentKeys, [outfit.name]: true }));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <section className="page-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Подбор образов</p>
          <h1>Создать подборку образов</h1>
        </div>
      </div>

      <form className="card form-card" onSubmit={handleSubmit}>
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
              <option value="evening">Вечер</option>
              <option value="sport">Спорт</option>
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
              placeholder="белый, черный, бежевый"
            />
          </label>

          <label>
            Предпочтительный стиль
            <input
              className="input"
              name="preferred_style"
              value={formValues.preferred_style}
              onChange={handleChange}
              placeholder="minimal"
            />
          </label>

          <label>
            Температура
            <input
              className="input"
              name="temperature"
              type="number"
              value={formValues.temperature}
              onChange={handleChange}
              placeholder="12"
            />
          </label>

          <label>
            Погода
            <select
              className="input"
              name="weather_condition"
              value={formValues.weather_condition}
              onChange={handleChange}
            >
              <option value="">Использовать тестовую погоду</option>
              <option value="sunny">Солнечно</option>
              <option value="cloudy">Облачно</option>
              <option value="clear">Ясно</option>
              <option value="rain">Дождь</option>
              <option value="snow">Снег</option>
              <option value="wind">Ветрено</option>
            </select>
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

          <label className="full-width">
            Ограничения
            <input
              className="input"
              name="constraints"
              value={formValues.constraints}
              onChange={handleChange}
              placeholder="no_heels, no_bright_colors"
            />
          </label>
        </div>

        <button type="submit" className="primary-button" disabled={loading}>
          {loading ? "Подбор..." : "Создать образы"}
        </button>
      </form>

      {error ? <p className="error-text">{error}</p> : null}

      {weather ? (
        <div className="card weather-card">
          <p className="eyebrow">Погодный контекст</p>
          <h3>
            {weather.temperature} °C | {translateWeather(weather.weather_condition)}
          </h3>
          <p className="muted-text">
            {weather.city || "Тестовый город"}
            {weather.season ? ` | ${translateSeason(weather.season)}` : ""}
          </p>
        </div>
      ) : null}

      <div className="outfit-grid">
        {generatedOutfits.map((outfit) => (
          <OutfitCard
            key={`${outfit.name}-${outfit.score}`}
            outfit={outfit}
            onSave={handleSave}
            isSaved={Boolean(savedKeys[outfit.name])}
          />
        ))}
      </div>

      {!loading && hasGenerated && generatedOutfits.length === 0 ? (
        <div className="card empty-state">
          {resultMessage || "Для выбранных параметров не найдено подходящих сочетаний."}
        </div>
      ) : null}
    </section>
  );
}
