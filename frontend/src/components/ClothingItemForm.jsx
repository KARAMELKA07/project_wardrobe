import { useEffect, useState } from "react";

import { analyzeItemImage } from "../api/itemsApi";
import { resolveAssetUrl } from "../api/client";
import {
  CATEGORY_OPTIONS,
  COLOR_OPTIONS,
  FIT_OPTIONS,
  INSULATION_OPTIONS,
  LAYER_LEVEL_OPTIONS,
  STYLE_OPTIONS,
  getColorLabel,
  getDefaultFitValue,
  getDefaultInsulationValue,
  getDefaultLayerLevelValue,
  getDefaultProtectionFlags,
  getSubcategoryLabel,
  getSubcategoryOptions,
  normalizeCatalogValue,
} from "../data/clothingOptions";
import useAuth from "../hooks/useAuth";
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

function buildSuggestedTitle(colors, baseTitle) {
  const cleanBaseTitle = baseTitle || "Новая вещь";
  if (!colors?.length) {
    return cleanBaseTitle;
  }

  return `${getColorLabel(colors[0])} ${cleanBaseTitle}`.trim();
}

export default function ClothingItemForm({
  initialValues,
  onSubmit,
  submitLabel,
  loading,
}) {
  const { token } = useAuth();
  const [formValues, setFormValues] = useState(mapInitialValues(initialValues));
  const [imageFile, setImageFile] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState("");
  const [analysisWarning, setAnalysisWarning] = useState("");
  const [analysisResult, setAnalysisResult] = useState(null);
  const [autoRemoveBackground, setAutoRemoveBackground] = useState(false);

  useEffect(() => {
    setFormValues(mapInitialValues(initialValues));
    setImageFile(null);
    setAnalysisLoading(false);
    setAnalysisError("");
    setAnalysisWarning("");
    setAnalysisResult(null);
    setAutoRemoveBackground(false);
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

  async function handleImageSelection(event) {
    const nextFile = event.target.files?.[0] || null;
    setImageFile(nextFile);
    setAnalysisError("");
    setAnalysisWarning("");
    setAnalysisResult(null);

    if (!nextFile) {
      setAutoRemoveBackground(false);
      return;
    }

    const formData = new FormData();
    formData.append("image", nextFile);

    setAnalysisLoading(true);
    try {
      const response = await analyzeItemImage(token, formData);
      applyImageAnalysis(response.analysis);
    } catch (requestError) {
      setAnalysisError(requestError.message);
      setAutoRemoveBackground(false);
    } finally {
      setAnalysisLoading(false);
    }
  }

  function applyImageAnalysis(analysis) {
    if (!analysis) {
      return;
    }

    setAnalysisResult(analysis);
    setAnalysisWarning((analysis.warnings || []).join(" "));
    setAutoRemoveBackground(Boolean(analysis.background_removed));

    const nextCategory = normalizeCatalogValue(analysis.category) || formValues.category;
    const nextSubcategory =
      normalizeCatalogValue(analysis.subcategory) || formValues.subcategory;
    const defaultMetadata = buildDefaultMetadata(nextCategory, nextSubcategory);
    const titleSuggestion = buildSuggestedTitle(
      analysis.colors,
      analysis.title_suggestion || getSubcategoryLabel(nextSubcategory),
    );

    setFormValues((currentValues) => ({
      ...currentValues,
      title: currentValues.title || titleSuggestion,
      category: nextCategory,
      subcategory: nextSubcategory,
      colors: analysis.colors?.length ? analysis.colors : currentValues.colors,
      styles: analysis.styles?.length ? analysis.styles : currentValues.styles,
      season: analysis.season || currentValues.season,
      formality: analysis.formality || currentValues.formality,
      fit: analysis.fit || defaultMetadata.fit,
      layer_level: analysis.layer_level || defaultMetadata.layer_level,
      insulation_rating: String(
        analysis.insulation_rating ?? defaultMetadata.insulation_rating,
      ),
      waterproof:
        analysis.waterproof ?? currentValues.waterproof ?? defaultMetadata.waterproof,
      windproof: analysis.windproof ?? currentValues.windproof ?? defaultMetadata.windproof,
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
    formData.append("auto_remove_background", String(autoRemoveBackground));

    if (formValues.image_url) {
      formData.append("image_url", formValues.image_url);
    }

    if (imageFile) {
      formData.append("image", imageFile);
    }

    await onSubmit(formData);
  }

  return (
    <form className="surface-card form-card" onSubmit={handleSubmit}>
      <div className="section-heading section-heading-stack">
        <div>
          <h1>{submitLabel}</h1>
        </div>
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
            <span className="field-label">Изображение вещи</span>
          </div>
          <label className="file-upload-button">
            <input
              type="file"
              accept=".png,.jpg,.jpeg,.webp"
              onChange={handleImageSelection}
              hidden
            />
            {imageFile ? imageFile.name : "Выберите файл"}
          </label>
        </div>

        <div className="field-block">
          <div className="field-heading">
            <span className="field-label">Защитные свойства</span>
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
                  aria-label={option.label}
                  title={option.label}
                >
                  <span
                    className="color-dot"
                    style={{
                      backgroundColor: option.hex,
                      borderColor: option.border,
                    }}
                  />
                </button>
              );
            })}
          </div>
        </div>

        <div className="field-block full-width">
          <div className="field-heading">
            <span className="field-label">Стили</span>
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

        <div className="field-block full-width">
          <div className="field-heading">
            <span className="field-label">ИИ-анализ изображения</span>
            <span className="field-helper">
              После загрузки фото система удалит фон, определит тип вещи и предложит характеристики.
            </span>
          </div>

          <label className={autoRemoveBackground ? "chip-button is-selected" : "chip-button"}>
            <input
              type="checkbox"
              checked={autoRemoveBackground}
              onChange={(event) => setAutoRemoveBackground(event.target.checked)}
              hidden
            />
            Удалить фон при сохранении
          </label>

          {analysisLoading ? (
            <p className="muted-text">Анализируем изображение и подбираем характеристики...</p>
          ) : null}

          {analysisError ? <p className="error-text">{analysisError}</p> : null}
          {analysisWarning ? <p className="muted-text">{analysisWarning}</p> : null}

          {analysisResult ? (
            <div className="analysis-summary">
              <span className="analysis-pill">
                Тип: {getSubcategoryLabel(analysisResult.subcategory) || "не определен"}
              </span>
              {(analysisResult.colors || []).map((color) => (
                <span key={color} className="analysis-pill">
                  Цвет: {getColorLabel(color)}
                </span>
              ))}
              {analysisResult.confidence ? (
                <span className="analysis-pill">
                  Точность: {(analysisResult.confidence * 100).toFixed(0)}%
                </span>
              ) : null}
            </div>
          ) : null}
        </div>
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

      <button type="submit" className="primary-button primary-button-wide" disabled={loading || analysisLoading}>
        {loading ? "Сохранение..." : submitLabel}
      </button>
    </form>
  );
}
