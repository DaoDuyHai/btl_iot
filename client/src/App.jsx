import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar.jsx';
import KioskPage from './pages/kiosk/KioskPage.jsx';
import AdminPage from './pages/admin/AdminPage.jsx';
import { socket } from './socket/socketClient.js';

function AppContent({ deviceStatus }) {
  const location = useLocation();
  const isAdmin = location.pathname.startsWith('/admin');

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Chỉ hiện Navbar chung khi ở trang Quản trị Thủ thư */}
      {isAdmin && <Navbar deviceStatus={deviceStatus} />}
      
      <main style={{ flex: 1 }}>
        <Routes>
          <Route path="/" element={<Navigate to="/kiosk" replace />} />
          <Route path="/kiosk" element={<KioskPage />} />
          <Route path="/admin" element={<AdminPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  const [deviceStatus, setDeviceStatus] = useState({ status: 'offline' });

  useEffect(() => {
    function handleDeviceStatus(data) {
      setDeviceStatus(data);
    }

    socket.on('device:status', handleDeviceStatus);
    return () => socket.off('device:status', handleDeviceStatus);
  }, []);

  return (
    <BrowserRouter>
      <AppContent deviceStatus={deviceStatus} />
    </BrowserRouter>
  );
}
