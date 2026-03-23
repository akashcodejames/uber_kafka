import { useEffect, useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { LogOut, MapPin, Navigation } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { useWebSocket } from "../hooks/useWebSocket";
import "leaflet/dist/leaflet.css";
import "../styles/dashboard.css"; // Ensure styles allow map height

// Fix for default Leaflet marker icons not loading in React
import iconUrl from "leaflet/dist/images/marker-icon.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";

const defaultIcon = L.icon({
  iconUrl,
  shadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = defaultIcon;

// Custom icon for Riders (using emoji/html)
const riderIcon = L.divIcon({
  html: `<div style="font-size: 24px;">🛵</div>`,
  className: "rider-icon",
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});


export default function MapDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [isRiderMode, setIsRiderMode] = useState(false);
  const [myLocation, setMyLocation] = useState([28.6139, 77.2090]); // Default to Delhi
  const [activeRiders, setActiveRiders] = useState({}); // { riderId: {lat, lng} }
  
  const token = localStorage.getItem("token");

  // Determine WS URL based on mode
  const wsUrl = isRiderMode
    ? `ws://localhost:8000/ws/rider?token=${token}`
    : `ws://localhost:8000/ws/user?token=${token}`;

  const { isConnected, lastMessage, sendMessage } = useWebSocket(wsUrl);

  const watchIdRef = useRef(null);

  // Handle incoming rider updates (only really matters in User mode)
  useEffect(() => {
    if (lastMessage && !isRiderMode) {
      setActiveRiders((prev) => ({
        ...prev,
        [lastMessage.rider_id]: { lat: lastMessage.lat, lng: lastMessage.lng },
      }));
    }
  }, [lastMessage, isRiderMode]);

  // Handle Geolocation API for Rider Mode
  useEffect(() => {
    if (isRiderMode) {
      if (!navigator.geolocation) {
        alert("Geolocation is not supported by your browser");
        setIsRiderMode(false);
        return;
      }

      // Start watching GPS
      watchIdRef.current = navigator.geolocation.watchPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          setMyLocation([lat, lng]);

          // Send to Kafka backend
          if (isConnected) {
            sendMessage({ lat, lng });
          }
        },
        (error) => {
          console.error("Error watching position", error);
        },
        { enableHighAccuracy: true, maximumAge: 0 }
      );
    } else {
      // User mode: get user location once just to center the map
      navigator.geolocation.getCurrentPosition((pos) => {
        setMyLocation([pos.coords.latitude, pos.coords.longitude]);
      });
    }

    return () => {
      // Clean up watch on mode change or unmount
      if (watchIdRef.current) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
    };
  }, [isRiderMode, isConnected, sendMessage]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  if (!user) {
    return (
      <div className="dashboard-loading">
        <div className="spinner large" />
      </div>
    );
  }

  return (
    <div className="dashboard-page flex-col">
      {/* Header Pipeline */}
      <header className="dashboard-nav">
        <div className="nav-brand">
          <MapPin className="brand-icon-sm" style={{ color: "var(--clr-accent-light)" }} />
          <span className="nav-brand-name">RideStream</span>
        </div>

        <div className="header-controls">
          <div className="mode-toggle">
            <span className={!isRiderMode ? "active" : ""}>User</span>
            <label className="switch">
              <input
                type="checkbox"
                checked={isRiderMode}
                onChange={(e) => {
                  setIsRiderMode(e.target.checked);
                  setActiveRiders({}); // clear riders when switching to rider mode
                }}
              />
              <span className="slider round"></span>
            </label>
            <span className={isRiderMode ? "active" : ""}>Rider</span>
          </div>

          <div className="user-profile">
            {user.picture ? (
              <img src={user.picture} alt="Profile" className="profile-img" />
            ) : (
              <div className="profile-placeholder">{user.email[0].toUpperCase()}</div>
            )}
            <div className="user-info">
              <span className="user-name">{user.name || "User"}</span>
            </div>
          </div>

          <button onClick={handleLogout} className="btn-logout">
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </div>
      </header>

      {/* Main Map Region */}
      <main className="map-container">
        {/* Connection Status Banner */}
        <div className={`connection-banner ${isConnected ? "connected" : "disconnected"}`}>
          <div className="status-indicator" />
          <span>
            {isConnected 
              ? `Connected to Real-Time Network (${isRiderMode ? "Streaming Location" : "Listening for Riders"})` 
              : "Reconnecting to Network..."}
          </span>
        </div>

        <MapContainer center={myLocation} zoom={14} style={{ height: "calc(100vh - 74px)", width: "100%", zIndex: 0 }}>
          <TileLayer
            attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {/* Automatically center map on user when location updates */}
          <MapCenterer position={myLocation} />

          {/* User's Own Location */}
          <Marker position={myLocation}>
            <Popup>
              {isRiderMode ? "Your Rider Location (Live)" : "Your Location"}
            </Popup>
          </Marker>

          {/* Render Active Riders on Map */}
          {!isRiderMode && Object.entries(activeRiders).map(([riderId, pos]) => (
            <Marker key={riderId} position={[pos.lat, pos.lng]} icon={riderIcon}>
              <Popup>Rider {riderId}</Popup>
            </Marker>
          ))}
        </MapContainer>
      </main>
    </div>
  );
}

// Helper component to center the map dynamically
function MapCenterer({ position }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(position, map.getZoom(), { animate: true, duration: 1.5 });
  }, [position, map]);
  return null;
}
