import { useEffect, useState } from "react";

import { resolveAssetUrl } from "../api/client";
import {
  CATEGORY_OPTIONS,
  COLOR_OPTIONS,
  FIT_OPTIONS,
  INSULATION_OPTIONS,
  LAYER_LEVEL_OPTIONS,
  STYLE_OPTIONS,
  getDefaultFitValue,
  getDefaultInsulationValue,
  getDefaultLayerLevelValue,
  getDefaultProtectionFlags,
  getSubcategoryLabel,
  getSubcategoryOptions,
  normalizeCatalogValue,
} from "../data/clothingOptions";
import {
  translateLayerLevel,
  translateFormality,
  translateFit,
  translateSeason,
} from "../utils/i18n";


const EMPTY_FORM = {
  title: "",
  category: "top",
  subcategory: "",
  colors: [],
  styles: [],
  season: "all-season",
  formality: "casual",
  fit: "balanced",
  layer_level: "base",
  insulation_rating: "0.6",
  waterproof: false,
  windproof: false,
  image_url: "",
};


function buildDefaultMetadata(category, subcategory) {
  const fit = getDefaultFitValue(subcategory);
  const layerLevel = getDefaultLayerLevelValue(subcategory, category);
  const insulationRating = getDefaultInsulationValue(subcategory);
  const protectionFlags = getDefaultProtectionFlags(subcategory);

  return {
    fit,
    layer_level: layerLevel,
    insulation_rating: insulationRating,
    waterproof: protectionFlags.waterproof,
    windproof: protectionFlags.windproof,
  };
}


function mapInitialValues(initialValues) {
  if (!initialValues) {
    return { ...EMPTY_FORM };
  }

  const category = normalizeCatalogValue(initialValues.category) || "top";
  const subcategory = normalizeCatalogValue(initialValues.subcategory);
  const defaultMetadata = buildDefaultMetadata(category, subcategory);

  return {
    title: initialValues.title || "",
    category,
    subcategory,
    colors: (initialValues.colors || []).map(normalizeCatalogValue),
    styles: (initialValues.styles || []).map(normalizeCatalogValue),
    season: initialValues.season || "all-season",
    formality: initialValues.formality || "casual",
    fit: initialValues.fit || defaultMetadata.fit,
    layer_level: initialValues.layer_level || defaultMetadata.layer_level,
    insulation_rating: String(
      initialValues.insulation_rating ?? defaultMetadata.insulation_rating,
    ),
    waterproof: Boolean(initialValues.waterproof ?? defaultMetadata.waterproof),
    windproof: Boolean(initialValues.windproof ?? defaultMetadata.windproof),
    image_url: initialValues.image_url || "",
  };
}


function toggleArrayValue(currentValues, value) {
  if (currentValues.includes(value)) {
    return currentValues.filter((entry) => entry !== value);
  }

  return [...currentValues, value];
}


export default function ClothingItemForm({
  initialValues,
  onSubmit,
  submitLabel,
  loading,
}) {
  const [formValues, setFormValues] = useState(mapInitialValues(initialValues));
  const [imageFile, setImageFile] = useState(null);

  useEffect(() => {
    setFormValues(mapInitialValues(initialValues));
    setImageFile(null);
  }, [initialValues]);

  const availableSubcategories = getSubcategoryOptions(formValues.category);

  function handleChange(event) {
    const { name, type, value, checked } = event.target;

    if (name === "category") {
      const normalizedCategory = normalizeCatalogValue(value);
      const nextSubcategories = getSubcategoryOptions(normalizedCategory);
      const currentSubcategory = normalizeCatalogValue(formValues.subcategory);
      const hasCurrentSubcategory = nextSubcategories.some(
        (entry) => entry.value === currentSubcategory,
      );

      setFormValues((currentValues) => ({
        ...currentValues,
        category: normalizedCategory,
        subcategory: hasCurrentSubcategory ? currentSubcategory : "",
        ...(hasCurrentSubcategory
          ? buildDefaultMetadata(normalizedCategory, currentSubcategory)
          : buildDefaultMetadata(normalizedCategory, "")),
      }));
      return;
    }

    if (name === "subcategory") {
      const normalizedSubcategory = normalizeCatalogValue(value);
      const defaultMetadata = buildDefaultMetadata(
        formValues.category,
        normalizedSubcategory,
      );

      setFormValues((currentValues) => ({
        ...currentValues,
        subcategory: normalizedSubcategory,
        ...defaultMetadata,
      }));
      return;
    }

    setFormValues((currentValues) => ({
      ...currentValues,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  function handleToggle(fieldName, value) {
    const normalizedValue = normalizeCatalogValue(value);

    setFormValues((currentValues) => ({
      ...currentValues,
      [fieldName]: toggleArrayValue(currentValues[fieldName], normalizedValue),
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const formData = new FormData();
    formData.append("title", formValues.title);
    formData.append("category", formValues.category);
    formData.append("subcategory", formValues.subcategory);
    formData.append("colors", JSON.stringify(formValues.colors));
    formData.append("styles", JSON.stringify(formValues.styles));
    formData.append("season", formValues.season);
    formData.append("formality", formValues.formality);
    formData.append("fit", formValues.fit);
    formData.append("layer_level", formValues.layer_level);
    formData.append("insulation_rating", formValues.insulation_rating);
    formData.append("waterproof", String(formValues.waterproof));
    formData.append("windproof", String(formValues.windproof));
    formData.append("material", "");

    if (formValues.image_url) {
      formData.append("image_url", formValues.image_url);
    }

    if (imageFile) {
      formData.append("image", imageFile);
    }

    await onSubmit(formData);
  }

  return (
    <form className="card form-card" onSubmit={handleSubmit}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">Гардероб</p>
          <h2>{submitLabel}</h2>
        </div>
        <p className="muted-text">
          Основные характеристики выбираются из каталога, чтобы сервису было проще
          собирать подходящие образы.
        </p>
      </div>

      <div className="form-grid">
        <label>
          Название
          <input
            className="input"
            name="title"
            value={formValues.title}
            onChange={handleChange}
            placeholder="Белая рубашка"
            required
          />
        </label>

        <label>
          Категория
          <select
            className="input"
            name="category"
            value={formValues.category}
            onChange={handleChange}
          >
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Подкатегория
          <select
            className="input"
            name="subcategory"
            value={formValues.subcategory}
            onChange={handleChange}
            required
          >
            <option value="">Выберите подкатегорию</option>
            {availableSubcategories.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Сезон
          <select
            className="input"
            name="season"
            value={formValues.season}
            onChange={handleChange}
          >
            <option value="all-season">{translateSeason("all-season")}</option>
            <option value="spring">{translateSeason("spring")}</option>
            <option value="summer">{translateSeason("summer")}</option>
            <option value="autumn">{translateSeason("autumn")}</option>
            <option value="winter">{translateSeason("winter")}</option>
          </select>
        </label>

        <label>
          Формальность
          <select
            className="input"
            name="formality"
            value={formValues.formality}
            onChange={handleChange}
          >
            <option value="casual">{translateFormality("casual")}</option>
            <option value="smart">{translateFormality("smart")}</option>
            <option value="formal">{translateFormality("formal")}</option>
          </select>
        </label>

        <label>
          Посадка и силуэт
          <select
            className="input"
            name="fit"
            value={formValues.fit}
            onChange={handleChange}
          >
            {FIT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Роль в слоистости
          <select
            className="input"
            name="layer_level"
            value={formValues.layer_level}
            onChange={handleChange}
          >
            {LAYER_LEVEL_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Уровень утепления
          <select
            className="input"
            name="insulation_rating"
            value={formValues.insulation_rating}
            onChange={handleChange}
          >
            {INSULATION_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <div className="field-block">
          <div className="field-heading">
            <span className="field-label">Защитные свойства</span>
            <span className="field-helper">
              Отметьте, если вещь реально защищает от дождя или ветра.
            </span>
          </div>
          <div className="chip-grid">
            <label className={formValues.waterproof ? "chip-button is-selected" : "chip-button"}>
              <input
                type="checkbox"
                name="waterproof"
                checked={formValues.waterproof}
                onChange={handleChange}
                hidden
              />
              Защита от дождя
            </label>
            <label className={formValues.windproof ? "chip-button is-selected" : "chip-button"}>
              <input
                type="checkbox"
                name="windproof"
                checked={formValues.windproof}
                onChange={handleChange}
                hidden
              />
              Защита от ветра
            </label>
          </div>
        </div>

        <div className="field-block full-width">
          <div className="field-heading">
            <span className="field-label">Цвета</span>
            <span className="field-helper">Можно выбрать несколько базовых цветов.</span>
          </div>
          <div className="color-picker-grid">
            {COLOR_OPTIONS.map((option) => {
              const selected = formValues.colors.includes(option.value);
              return (
                <button
                  key={option.value}
                  type="button"
                  className={selected ? "color-swatch is-selected" : "color-swatch"}
                  onClick={() => handleToggle("colors", option.value)}
                >
                  <span
                    className="color-dot"
                    style={{
                      backgroundColor: option.hex,
                      borderColor: option.border,
                    }}
                  />
                  <span>{option.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="field-block full-width">
          <div className="field-heading">
            <span className="field-label">Стили</span>
            <span className="field-helper">Выберите один или несколько подходящих стилей.</span>
          </div>
          <div className="chip-grid">
            {STYLE_OPTIONS.map((option) => {
              const selected = formValues.styles.includes(option.value);
              return (
                <button
                  key={option.value}
                  type="button"
                  className={selected ? "chip-button is-selected" : "chip-button"}
                  onClick={() => handleToggle("styles", option.value)}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        <label className="file-input-wrapper full-width">
          Изображение вещи
          <input
            className="input"
            type="file"
            accept=".png,.jpg,.jpeg,.webp"
            onChange={(event) => setImageFile(event.target.files?.[0] || null)}
          />
        </label>
      </div>

      {formValues.image_url ? (
        <div className="inline-media">
          <img
            src={resolveAssetUrl(formValues.image_url)}
            alt={formValues.title}
            className="inline-thumbnail"
          />
          <p className="muted-text">
            Текущее изображение сохранится, если не загружать новое. Подкатегория:{" "}
            {getSubcategoryLabel(formValues.subcategory)}. Посадка:{" "}
            {translateFit(formValues.fit)}. Слой:{" "}
            {translateLayerLevel(formValues.layer_level)}.
          </p>
        </div>
      ) : null}

      <button type="submit" className="primary-button" disabled={loading}>
        {loading ? "Сохранение..." : submitLabel}
      </button>
    </form>
  );
}
