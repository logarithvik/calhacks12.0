import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import TrialDetail from './pages/TrialDetail';
import SummaryEdit from './pages/SummaryEdit';
import VideoViewer from './pages/VideoViewer';
import './index.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trial/:id"
              element={
                <ProtectedRoute>
                  <TrialDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trial/:id/summary/edit"
              element={
                <ProtectedRoute>
                  <SummaryEdit />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trial/:id/video/:contentId"
              element={
                <ProtectedRoute>
                  <VideoViewer />
                </ProtectedRoute>
              }
            />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
