import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import GuestRoute from "./components/GuestRoute";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import AddClothingItemPage from "./pages/AddClothingItemPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import ClothingItemDetailsPage from "./pages/ClothingItemDetailsPage";
import DashboardPage from "./pages/DashboardPage";
import EditClothingItemPage from "./pages/EditClothingItemPage";
import LoginPage from "./pages/LoginPage";
import OutfitGeneratorPage from "./pages/OutfitGeneratorPage";
import RegisterPage from "./pages/RegisterPage";
import SavedOutfitsPage from "./pages/SavedOutfitsPage";
import WardrobePage from "./pages/WardrobePage";


function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route
            path="/login"
            element={
              <GuestRoute>
                <LoginPage />
              </GuestRoute>
            }
          />
          <Route
            path="/register"
            element={
              <GuestRoute>
                <RegisterPage />
              </GuestRoute>
            }
          />

          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/wardrobe" element={<WardrobePage />} />
              <Route path="/wardrobe/add" element={<AddClothingItemPage />} />
              <Route path="/wardrobe/:itemId" element={<ClothingItemDetailsPage />} />
              <Route path="/wardrobe/:itemId/edit" element={<EditClothingItemPage />} />
              <Route path="/generate" element={<OutfitGeneratorPage />} />
              <Route path="/outfits" element={<SavedOutfitsPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}


export default App;
