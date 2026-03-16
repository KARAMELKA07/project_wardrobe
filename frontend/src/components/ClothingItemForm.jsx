import { useEffect, useState } from "react";

import { resolveAssetUrl } from "../api/client";
import {
  CATEGORY_OPTIONS,
  COLOR_OPTIONS,
  STYLE_OPTIONS,
  getSubcategoryLabel,
  getSubcategoryOptions,
  normalizeCatalogValue,
} from "../data/clothingOptions";
import {
  translateFormality,
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
  image_url: "",
};


function mapInitialValues(initialValues) {
  if (!initialValues) {
    return { ...EMPTY_FORM };
  }

  return {
    title: initialValues.title || "",
    category: normalizeCatalogValue(initialValues.category) || "top",
    subcategory: normalizeCatalogValue(initialValues.subcategory),
    colors: (initialValues.colors || []).map(normalizeCatalogValue),
    styles: (initialValues.styles || []).map(normalizeCatalogValue),
    season: initialValues.season || "all-season",
    formality: initialValues.formality || "casual",
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
    const { name, value } = event.target;

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
      }));
      return;
    }

    setFormValues((currentValues) => ({
      ...currentValues,
      [name]: value,
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
            Текущее изображение сохранится, если не загружать новое. Подкатегория:
            {" "}
            {getSubcategoryLabel(formValues.subcategory)}
          </p>
        </div>
      ) : null}

      <button type="submit" className="primary-button" disabled={loading}>
        {loading ? "Сохранение..." : submitLabel}
      </button>
    </form>
  );
}
