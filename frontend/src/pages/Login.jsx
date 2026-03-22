import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";
import GoogleButton from "../components/GoogleButton";
import "../styles/auth.css";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login", form);
      login(data.access_token, data.user);
      navigate("/dashboard");
    } catch (err) {
      setError(
        err.response?.data?.detail || "Login failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = () => {
    // Redirect browser to backend which redirects to Google OAuth
    window.location.href = "http://localhost:8000/auth/google";
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Logo / Brand */}
        <div className="brand">
          <div className="brand-icon">🔐</div>
          <h1 className="brand-name">AuthFlow</h1>
          <p className="brand-tagline">Welcome back</p>
        </div>

        {/* Google OAuth Button */}
        <GoogleButton onClick={handleGoogle} label="Continue with Google" />

        {/* Divider */}
        <div className="divider">
          <span>or sign in with email</span>
        </div>

        {/* Error Banner */}
        {error && <div className="error-banner">{error}</div>}

        {/* Email/Password Form */}
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              name="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={handleChange}
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              name="password"
              placeholder="••••••••"
              value={form.password}
              onChange={handleChange}
              required
              autoComplete="current-password"
            />
          </div>

          <button
            id="login-submit"
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? <span className="spinner" /> : "Sign In"}
          </button>
        </form>

        <p className="auth-link">
          Don&apos;t have an account?{" "}
          <Link to="/signup">Create one</Link>
        </p>
      </div>
    </div>
  );
}
