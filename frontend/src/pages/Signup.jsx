import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";
import GoogleButton from "../components/GoogleButton";
import "../styles/auth.css";

export default function Signup() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [form, setForm] = useState({ email: "", password: "", name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      const { data } = await api.post("/auth/register", form);
      login(data.access_token, data.user);
      navigate("/dashboard");
    } catch (err) {
      setError(
        err.response?.data?.detail || "Registration failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = () => {
    window.location.href = "http://localhost:8000/auth/google";
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Logo / Brand */}
        <div className="brand">
          <div className="brand-icon">🔐</div>
          <h1 className="brand-name">AuthFlow</h1>
          <p className="brand-tagline">Create your account</p>
        </div>

        {/* Google OAuth Button */}
        <GoogleButton onClick={handleGoogle} label="Sign up with Google" />

        {/* Divider */}
        <div className="divider">
          <span>or sign up with email</span>
        </div>

        {/* Error Banner */}
        {error && <div className="error-banner">{error}</div>}

        {/* Signup Form */}
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="signup-name">Full Name</label>
            <input
              id="signup-name"
              type="text"
              name="name"
              placeholder="John Doe"
              value={form.name}
              onChange={handleChange}
              autoComplete="name"
            />
          </div>

          <div className="form-group">
            <label htmlFor="signup-email">Email</label>
            <input
              id="signup-email"
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
            <label htmlFor="signup-password">Password</label>
            <input
              id="signup-password"
              type="password"
              name="password"
              placeholder="At least 8 characters"
              value={form.password}
              onChange={handleChange}
              required
              minLength={8}
              autoComplete="new-password"
            />
            <span className="field-hint">
              Stored securely with bcrypt hashing
            </span>
          </div>

          <button
            id="signup-submit"
            type="submit"
            className="btn-primary"
            disabled={loading}
          >
            {loading ? <span className="spinner" /> : "Create Account"}
          </button>
        </form>

        <p className="auth-link">
          Already have an account?{" "}
          <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
