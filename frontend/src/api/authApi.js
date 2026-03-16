import { apiFetch } from "./client";


export function registerUser(payload) {
  return apiFetch("/auth/register", {
    method: "POST",
    body: payload,
  });
}


export function loginUser(payload) {
  return apiFetch("/auth/login", {
    method: "POST",
    body: payload,
  });
}


export function fetchCurrentUser(token) {
  return apiFetch("/auth/me", {
    token,
  });
}
