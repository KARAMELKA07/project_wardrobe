import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";

import ClothingItemDetailsModal from "./components/ClothingItemDetailsModal";
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

function AppRoutes() {
  const location = useLocation();
  const backgroundLocation = location.state?.backgroundLocation;

  return (
    <>
      <Routes location={backgroundLocation || location}>
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

      {backgroundLocation ? (
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/wardrobe/:itemId" element={<ClothingItemDetailsModal />} />
          </Route>
        </Routes>
      ) : null}
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
