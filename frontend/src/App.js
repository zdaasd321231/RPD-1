import React, { useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import LoginPage from "./components/LoginPage";
import Dashboard from "./components/Dashboard";
import RDPClient from "./components/RDPClient";
import FileManager from "./components/FileManager";
import SessionMonitor from "./components/SessionMonitor";
import LogsViewer from "./components/LogsViewer";
import Settings from "./components/Settings";
import Sidebar from "./components/Sidebar";
import { Toaster } from "./components/ui/sonner";

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
};

const AppContent = () => {
  const { isAuthenticated } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      <main className={`flex-1 transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-16'}`}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/rdp" element={<RDPClient />} />
          <Route path="/files" element={<FileManager />} />
          <Route path="/sessions" element={<SessionMonitor />} />
          <Route path="/logs" element={<LogsViewer />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/*" element={
              <ProtectedRoute>
                <AppContent />
              </ProtectedRoute>
            } />
          </Routes>
        </BrowserRouter>
        <Toaster />
      </div>
    </AuthProvider>
  );
}

export default App;