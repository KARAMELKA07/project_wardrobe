import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import useAuth from "../hooks/useAuth";


export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [formValues, setFormValues] = useState({
    name: "",
    email: "",
    password: "",
    city: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(event) {
    const { name, value } = event.target;
    setFormValues((currentValues) => ({ ...currentValues, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      await register(formValues);
      navigate("/");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-card-inner">
          <h1>Регистрация</h1>
          <p className="auth-description">
            Создайте аккаунт, чтобы собрать цифровой гардероб и тестировать подбор образов.
          </p>

          <label>
            Имя
            <input
              className="input"
              name="name"
              value={formValues.name}
              onChange={handleChange}
              required
            />
          </label>

          <label>
            Город
            <input
              className="input"
              name="city"
              value={formValues.city}
              onChange={handleChange}
              placeholder="Москва"
            />
          </label>

          <label>
            Email
            <input
              className="input"
              type="email"
              name="email"
              value={formValues.email}
              onChange={handleChange}
              required
            />
          </label>

          <label>
            Пароль
            <input
              className="input"
              type="password"
              name="password"
              value={formValues.password}
              onChange={handleChange}
              required
            />
          </label>

          {error ? <p className="error-text">{error}</p> : null}

          <button type="submit" className="primary-button" disabled={loading}>
            {loading ? "Создание..." : "Создать аккаунт"}
          </button>

          <p className="auth-link-text">
            Уже есть аккаунт? <Link to="/login">Войти</Link>
          </p>
        </div>
      </form>
    </div>
  );
}
