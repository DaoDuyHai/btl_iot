import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import KioskPage from './pages/kiosk/KioskPage.jsx';
import AdminPage from './pages/admin/AdminPage.jsx';

function AppContent() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <main style={{ flex: 1 }}>
        <Routes>
          <Route path="/" element={<Navigate to="/kiosk" replace />} />
          <Route path="/kiosk" element={<KioskPage />} />
          <Route path="/admin" element={<AdminPage />} />
          {/* Tự động chuyển hướng nếu người dùng gõ nhầm /kiosk/admin hoặc URL lạ */}
          <Route path="/kiosk/admin" element={<Navigate to="/admin" replace />} />
          <Route path="*" element={<Navigate to="/kiosk" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
