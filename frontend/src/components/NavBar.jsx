import { NavLink } from "react-router-dom";


const NAV_ITEMS = [
  { to: "/", label: "Главная" },
  { to: "/wardrobe", label: "Гардероб" },
  { to: "/generate", label: "Подбор образов" },
  { to: "/outfits", label: "Сохраненные образы" },
];


export default function NavBar() {
  return (
    <nav className="nav-panel">
      <div className="nav-brand">
        <h1 className="nav-title">
          <span>Сервис подбора</span>
          <span>образов</span>
        </h1>
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
