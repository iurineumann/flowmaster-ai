// frontend/src/components/Layout.tsx
import React from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { LayoutDashboard, LogOut, Bell, Settings } from 'lucide-react';
import ChatWidget from './ChatWidget';

const Layout: React.FC = () => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    // O App.tsx (componente pai) detectará a mudança de autenticação e renderizará o Login
  };

  return (
    <div className="min-h-screen bg-gray-50 text-foreground dark:bg-gray-950">
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4 flex justify-between items-center sticky top-0 z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="bg-primary/10 p-2 rounded-lg">
            <LayoutDashboard className="w-6 h-6 text-primary" />
          </div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-white">FlowMaster AI</h1>
        </div>
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/settings')}
            className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full"
            title="Configurações"
          >
            <Settings className="w-5 h-5" />
          </button>
          
          <button className="p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full relative" title="Notificações">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>
          
          <div className="h-6 w-px bg-gray-200 dark:bg-gray-700"></div>
          
          <button 
            onClick={handleLogout} 
            className="text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-primary flex items-center gap-2 transition-colors"
          >
            <LogOut className="w-4 h-4" /> Sair
          </button>
        </div>
      </header>

      {/* O conteúdo da rota (Dashboard ou Settings) será renderizado aqui */}
      <Outlet />

      <ChatWidget />
    </div>
  );
};

export default Layout;