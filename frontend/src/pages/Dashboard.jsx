import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "../styles/dashboard.css";

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout, loading } = useAuth();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!loading && !user) {
      navigate("/login", { replace: true });
    }
  }, [loading, user, navigate]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  if (loading || !user) {
    return (
      <div className="dashboard-loading">
        <div className="spinner large" />
      </div>
    );
  }

  const authMethod = user.google_id ? "Google OAuth" : "Email & Password";
  const initials = user.name
    ? user.name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
    : user.email[0].toUpperCase();

  return (
    <div className="dashboard-page">
      {/* Top navigation bar */}
      <nav className="dashboard-nav">
        <div className="nav-brand">
          <span className="brand-icon-sm">🔐</span>
          <span className="nav-brand-name">AuthFlow</span>
        </div>
        <button
          id="logout-btn"
          className="btn-logout"
          onClick={handleLogout}
        >
          Sign Out
        </button>
      </nav>

      {/* Main content */}
      <main className="dashboard-main">
        <div className="profile-card">
          {/* Avatar */}
          <div className="avatar-wrapper">
            {user.picture ? (
              <img
                src={user.picture}
                alt={user.name || user.email}
                className="avatar-img"
              />
            ) : (
              <div className="avatar-initials">{initials}</div>
            )}
            <div className="avatar-badge">✓</div>
          </div>

          {/* User Info */}
          <h2 className="profile-name">{user.name || "Anonymous User"}</h2>
          <p className="profile-email">{user.email}</p>

          {/* Auth method pill */}
          <span className={`auth-badge ${user.google_id ? "google" : "email"}`}>
            {user.google_id ? "🔵" : "🔒"} {authMethod}
          </span>

          {/* Stats grid */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">User ID</div>
              <div className="stat-value">#{user.id}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Auth Method</div>
              <div className="stat-value">
                {user.google_id ? "Google" : "Email"}
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Password</div>
              <div className="stat-value">
                {user.google_id ? "N/A" : "Bcrypt"}
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Token</div>
              <div className="stat-value">JWT HS256</div>
            </div>
          </div>

          {/* Security info */}
          <div className="security-info">
            <h3>🛡️ Security Details</h3>
            <ul>
              <li>
                <span className="check">✓</span>
                {user.google_id
                  ? "Authenticated via Google OAuth 2.0 (Authorization Code Flow)"
                  : "Password hashed with bcrypt (never stored in plaintext)"}
              </li>
              <li>
                <span className="check">✓</span>
                Profile stored in SQLite via SQLAlchemy ORM
              </li>
              <li>
                <span className="check">✓</span>
                Session managed with HS256 JWT access token
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
