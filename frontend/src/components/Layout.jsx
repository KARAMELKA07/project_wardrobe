import { Link, Outlet } from "react-router-dom";

import useAuth from "../hooks/useAuth";
import NavBar from "./NavBar";


export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <NavBar />

      <main className="content-shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">Авторизация</p>
            <h2 className="page-title">{user?.name || "Пользователь"}</h2>
            <p className="muted-text">
              {user?.email}
              {user?.city ? ` | ${user.city}` : ""}
            </p>
          </div>

          <div className="topbar-actions">
            <Link to="/wardrobe/add" className="secondary-button">
              Добавить вещь
            </Link>
            <button type="button" className="ghost-button" onClick={logout}>
              Выйти
            </button>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  );
}
