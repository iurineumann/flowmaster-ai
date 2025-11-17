// frontend/src/App.tsx

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './services/AuthContext';
import Login from './Login';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import SettingsPage from './pages/SettingsPage';
import AdminStatsPage from './pages/AdminStatsPage'; // ✅ NOVO

/**
 * Componente de Rota Privada
 */
const PrivateRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

// TODO: Implementar lógica de Rota de Admin (verificar role do usuário)
const AdminRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
    // const { userRole } = useAuth(); // Exemplo
    // return userRole === 'admin' ? children : <Navigate to="/" replace />;
    return children; // Por enquanto, permite acesso
};

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/" replace /> : <Login />} 
      />
      
      {/* Rotas Protegidas (Layout Principal) */}
      <Route 
        path="/" 
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<DashboardPage />} /> 
        <Route path="settings" element={<SettingsPage />} />
        
        {/* ✅ NOVA ROTA DE ADMIN */}
        <Route 
          path="admin" 
          element={
            <AdminRoute>
              <AdminStatsPage />
            </AdminRoute>
          } 
        />
        
      </Route>

    </Routes>
  );
}

export default App;