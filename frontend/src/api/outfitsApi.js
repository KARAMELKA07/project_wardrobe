import { apiFetch } from "./client";


export function generateOutfits(token, payload) {
  return apiFetch("/outfits/generate", {
    method: "POST",
    token,
    body: payload,
  });
}


export function fetchSavedOutfits(token) {
  return apiFetch("/outfits", {
    token,
  });
}


export function saveOutfit(token, payload) {
  return apiFetch("/outfits", {
    method: "POST",
    token,
    body: payload,
  });
}


export function uploadOutfitPhoto(token, outfitId, formData) {
  return apiFetch(`/outfits/${outfitId}/photo`, {
    method: "POST",
    token,
    body: formData,
    isFormData: true,
  });
}


export function sendOutfitFeedback(token, outfitId, reaction) {
  return apiFetch(`/outfits/${outfitId}/feedback`, {
    method: "POST",
    token,
    body: { reaction },
  });
}
