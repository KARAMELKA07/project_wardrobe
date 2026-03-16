import { createContext, useEffect, useState } from "react";

import { fetchCurrentUser, loginUser, registerUser } from "../api/authApi";


const STORAGE_KEY = "wardrobe_access_token";

export const AuthContext = createContext(null);


export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem(STORAGE_KEY));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(localStorage.getItem(STORAGE_KEY)));

  useEffect(() => {
    async function loadProfile() {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetchCurrentUser(token);
        setUser(response.user);
      } catch (_error) {
        localStorage.removeItem(STORAGE_KEY);
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    loadProfile();
  }, [token]);

  async function login(credentials) {
    const response = await loginUser(credentials);
    localStorage.setItem(STORAGE_KEY, response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    return response;
  }

  async function register(payload) {
    const response = await registerUser(payload);
    localStorage.setItem(STORAGE_KEY, response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    return response;
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
  }

  async function refreshProfile() {
    if (!token) {
      return null;
    }
    const response = await fetchCurrentUser(token);
    setUser(response.user);
    return response.user;
  }

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        loading,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
