import { Navigate } from "react-router-dom";

import useAuth from "../hooks/useAuth";


export default function GuestRoute({ children }) {
  const { token, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="page-shell">
        <div className="card centered-card">Загрузка приложения...</div>
      </div>
    );
  }

  if (token && user) {
    return <Navigate to="/" replace />;
  }

  return children;
}
