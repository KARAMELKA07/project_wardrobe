import { NavLink } from "react-router-dom";


const NAV_ITEMS = [
  { to: "/", label: "Главная" },
  { to: "/wardrobe", label: "Гардероб" },
  { to: "/generate", label: "Подбор образов" },
  { to: "/outfits", label: "Сохранённые образы" },
  { to: "/analytics", label: "Аналитика" },
];


export default function NavBar() {
  return (
    <nav className="nav-panel">
      <div>
        <p className="eyebrow">Цифровой гардероб</p>
        <h1 className="nav-title">Сервис подбора образов</h1>
      </div>

      <div className="nav-links">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              isActive ? "nav-link nav-link-active" : "nav-link"
            }
          >
            {item.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
