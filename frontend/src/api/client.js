export const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000/api";

const PLACEHOLDER_BY_CATEGORY = {
  top: "/uploads/placeholders/top.svg",
  bottom: "/uploads/placeholders/bottom.svg",
  shoes: "/uploads/placeholders/shoes.svg",
  outerwear: "/uploads/placeholders/outerwear.svg",
  accessory: "/uploads/placeholders/accessory.svg",
};


export async function apiFetch(path, options = {}) {
  const {
    method = "GET",
    token,
    body,
    isFormData = false,
  } = options;

  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body
      ? isFormData
        ? body
        : JSON.stringify(body)
      : undefined,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || "Не удалось выполнить запрос.");
  }

  return payload;
}


export function resolveAssetUrl(assetPath) {
  if (!assetPath) {
    return null;
  }
  if (assetPath.startsWith("http://") || assetPath.startsWith("https://")) {
    return assetPath;
  }

  const assetBaseUrl = API_URL.replace(/\/api$/, "");
  return `${assetBaseUrl}${assetPath}`;
}


export function getCategoryPlaceholderUrl(category = "top") {
  const normalizedCategory = String(category || "top").toLowerCase();
  return resolveAssetUrl(
    PLACEHOLDER_BY_CATEGORY[normalizedCategory] || PLACEHOLDER_BY_CATEGORY.top,
  );
}


export function resolveItemImageUrl(item, fallbackCategory) {
  if (item?.image_url) {
    return resolveAssetUrl(item.image_url);
  }

  return getCategoryPlaceholderUrl(item?.category || fallbackCategory);
}
