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


export function sendOutfitFeedback(token, outfitId, reaction) {
  return apiFetch(`/outfits/${outfitId}/feedback`, {
    method: "POST",
    token,
    body: { reaction },
  });
}
