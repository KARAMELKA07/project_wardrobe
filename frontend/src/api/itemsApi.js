import { apiFetch } from "./client";


export function fetchItems(token) {
  return apiFetch("/items", { token });
}


export function fetchItemById(token, itemId) {
  return apiFetch(`/items/${itemId}`, { token });
}


export function createItem(token, formData) {
  return apiFetch("/items", {
    method: "POST",
    token,
    body: formData,
    isFormData: true,
  });
}


export function updateItem(token, itemId, formData) {
  return apiFetch(`/items/${itemId}`, {
    method: "PUT",
    token,
    body: formData,
    isFormData: true,
  });
}


export function deleteItem(token, itemId) {
  return apiFetch(`/items/${itemId}`, {
    method: "DELETE",
    token,
  });
}
