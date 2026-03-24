import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { LogOut, Map, Navigation, Wifi, WifiOff, MapPin } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { useWebSocket } from "../hooks/useWebSocket";
import "leaflet/dist/leaflet.css";
import "../styles/dashboard.css"; 

import iconUrl from "leaflet/dist/images/marker-icon.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";

const defaultIcon = L.icon({
  iconUrl,
  shadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = defaultIcon;

// Custom animated ping icon for Riders
const createRiderIcon = () => {
  return L.divIcon({
    html: `
      <div class="rider-marker-container">
        <div class="rider-marker-pulse"></div>
        <div class="rider-marker-dot">🛵</div>
      </div>
    `,
    className: "custom-rider-marker",
    iconSize: [40, 40],
    iconAnchor: [20, 20],
  });
};

export default function MapDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [isRiderMode, setIsRiderMode] = useState(false);
  const [myLocation, setMyLocation] = useState([28.6139, 77.2090]); // Default
  const [activeRiders, setActiveRiders] = useState({}); 
  
  const token = localStorage.getItem("token");

  const wsUrl = isRiderMode
    ? `ws://localhost:8000/ws/rider?token=${token}`
    : `ws://localhost:8000/ws/user?token=${token}`;

  const { isConnected, lastMessage, sendMessage } = useWebSocket(wsUrl);
  const watchIdRef = useRef(null);
  const riderIconAttr = createRiderIcon();
  const lastSentTimeRef = useRef(0); // For throttling WebSocket usage

  useEffect(() => {
    if (lastMessage && !isRiderMode) {
      setActiveRiders((prev) => ({
        ...prev,
        [lastMessage.rider_id]: { lat: lastMessage.lat, lng: lastMessage.lng },
      }));
    }
  }, [lastMessage, isRiderMode]);

  useEffect(() => {
    if (!navigator.geolocation) {
      console.warn("Geolocation is not supported by your browser");
      return;
    }

    watchIdRef.current = navigator.geolocation.watchPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        setMyLocation([lat, lng]);

        // Rate limit: Only send to Kafka backend max once every 2000 milliseconds (2 seconds)
        if (isRiderMode && isConnected) {
          const now = Date.now();
          if (now - lastSentTimeRef.current >= 2000) {
            sendMessage({ lat, lng });
            lastSentTimeRef.current = now;
          }
        }
      },
      (error) => console.error("Error watching position", error),
      { enableHighAccuracy: true, maximumAge: 0 }
    );

    return () => {
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
    <div className="fullscreen-map-wrapper">
      
      {/* Background Map - Takes full screen */}
      <MapContainer 
        center={myLocation} 
        zoom={14} 
        zoomControl={false}
        className="leaflet-fullscreen"
      >
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />
        <MapCenterer position={myLocation} />
        <Marker position={myLocation}>
          <Popup>{isRiderMode ? "Broadcasting Location" : "You are here"}</Popup>
        </Marker>
        {!isRiderMode && Object.entries(activeRiders).map(([riderId, pos]) => (
          <Marker key={riderId} position={[pos.lat, pos.lng]} icon={riderIconAttr}>
            <Popup>Rider {riderId}</Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Floating UI Elements */}
      <div className="floating-ui-layer">
        
        {/* Top Header - Glassmorphic */}
        <header className="glass-header">
          <div className="brand-logo">
            <div className="logo-icon-wrapper">
              <MapPin size={22} className="logo-icon" />
            </div>
            <span className="brand-text">RideStream</span>
          </div>

          <div className="header-actions">
            <div className={`status-pill ${isConnected ? 'online' : 'offline'}`}>
              <div className="pulse-dot"></div>
              <span>{isConnected ? 'Connected' : 'Connecting...'}</span>
            </div>
            
            <div className="user-profile-mini">
              {user.picture ? (
                <img src={user.picture} alt="Profile" className="mini-avatar" />
              ) : (
                <div className="mini-avatar empty">{user.name?.[0] || "U"}</div>
              )}
            </div>

            <button onClick={handleLogout} className="glass-btn icon-only" title="Logout">
              <LogOut size={18} />
            </button>
          </div>
        </header>

        {/* Bottom floating dock for mode toggle */}
        <div className="floating-dock-wrapper">
          <div className="glass-dock">
            <button 
              className={`dock-btn ${!isRiderMode ? 'active' : ''}`}
              onClick={() => { setIsRiderMode(false); setActiveRiders({}); }}
            >
              <Map size={20} />
              <span>Looking for rides</span>
            </button>

            <div className="dock-divider"></div>

            <button 
              className={`dock-btn rider-btn ${isRiderMode ? 'active' : ''}`}
              onClick={() => { setIsRiderMode(true); setActiveRiders({}); }}
            >
              <Navigation size={20} />
              <span>I am riding</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

function MapCenterer({ position }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo(position, map.getZoom(), { animate: true, duration: 2 });
  }, [position, map]);
  return null;
}
