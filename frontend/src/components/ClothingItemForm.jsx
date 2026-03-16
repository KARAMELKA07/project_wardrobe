import { useEffect, useState } from "react";

import { resolveAssetUrl } from "../api/client";
import {
  translateCategory,
  translateFormality,
  translateSeason,
} from "../utils/i18n";


const EMPTY_FORM = {
  title: "",
  category: "top",
  subcategory: "",
  colors: "",
  styles: "",
  season: "all-season",
  formality: "casual",
  material: "",
  image_url: "",
};


function mapInitialValues(initialValues) {
  if (!initialValues) {
    return { ...EMPTY_FORM };
  }

  return {
    title: initialValues.title || "",
    category: initialValues.category || "top",
    subcategory: initialValues.subcategory || "",
    colors: (initialValues.colors || []).join(", "),
    styles: (initialValues.styles || []).join(", "),
    season: initialValues.season || "all-season",
    formality: initialValues.formality || "casual",
    material: initialValues.material || "",
    image_url: initialValues.image_url || "",
  };
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

  function handleChange(event) {
    const { name, value } = event.target;
    setFormValues((currentValues) => ({
      ...currentValues,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    const formData = new FormData();
    Object.entries(formValues).forEach(([key, value]) => {
      if (key === "image_url") {
        if (value) {
          formData.append(key, value);
        }
        return;
      }

      formData.append(key, value);
    });

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
          Цвета и стили можно вводить через запятую.
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
            <option value="top">{translateCategory("top")}</option>
            <option value="bottom">{translateCategory("bottom")}</option>
            <option value="shoes">{translateCategory("shoes")}</option>
            <option value="outerwear">{translateCategory("outerwear")}</option>
            <option value="accessory">{translateCategory("accessory")}</option>
          </select>
        </label>

        <label>
          Подкатегория
          <input
            className="input"
            name="subcategory"
            value={formValues.subcategory}
            onChange={handleChange}
            placeholder="Пиджак, кеды, юбка"
          />
        </label>

        <label>
          Материал
          <input
            className="input"
            name="material"
            value={formValues.material}
            onChange={handleChange}
            placeholder="Хлопок"
          />
        </label>

        <label>
          Цвета
          <input
            className="input"
            name="colors"
            value={formValues.colors}
            onChange={handleChange}
            placeholder="white, blue"
          />
        </label>

        <label>
          Стили
          <input
            className="input"
            name="styles"
            value={formValues.styles}
            onChange={handleChange}
            placeholder="classic, minimal"
          />
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

        <label className="file-input-wrapper">
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
            Текущее изображение сохранится, если не загружать новое.
          </p>
        </div>
      ) : null}

      <button type="submit" className="primary-button" disabled={loading}>
        {loading ? "Сохранение..." : submitLabel}
      </button>
    </form>
  );
}
