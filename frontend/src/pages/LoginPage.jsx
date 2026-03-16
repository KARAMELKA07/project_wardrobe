import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import useAuth from "../hooks/useAuth";


export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formValues, setFormValues] = useState({ email: "", password: "" });
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
      await login(formValues);
      navigate("/");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <form className="card auth-card" onSubmit={handleSubmit}>
        <p className="eyebrow">Цифровой гардероб</p>
        <h1>Вход</h1>
        <p className="muted-text">
          Войдите в сервис для управления гардеробом и подбора образов.
        </p>

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
          {loading ? "Вход..." : "Войти"}
        </button>

        <p className="muted-text">
          Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
        </p>
      </form>
    </div>
  );
}
