import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { 
  LayoutDashboard, 
  Monitor, 
  FolderOpen, 
  Users, 
  FileText, 
  Settings, 
  LogOut,
  ChevronLeft,
  ChevronRight,
  Shield
} from 'lucide-react';

const Sidebar = ({ isOpen, onToggle }) => {
  const location = useLocation();
  const { logout, user } = useAuth();

  const menuItems = [
    { path: '/', icon: LayoutDashboard, label: 'Панель управления', badge: null },
    { path: '/rdp', icon: Monitor, label: 'RDP Клиент', badge: null },
    { path: '/files', icon: FolderOpen, label: 'Файлы', badge: null },
    { path: '/sessions', icon: Users, label: 'Сессии', badge: 2 },
    { path: '/logs', icon: FileText, label: 'Логи', badge: null },
    { path: '/settings', icon: Settings, label: 'Настройки', badge: null }
  ];

  const handleLogout = () => {
    logout();
  };

  return (
    <div className={`fixed left-0 top-0 h-full bg-black/60 backdrop-blur-lg border-r border-purple-500/20 transition-all duration-300 z-50 ${isOpen ? 'w-64' : 'w-16'}`}>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-4 border-b border-purple-500/20">
          <div className="flex items-center justify-between">
            <div className={`flex items-center space-x-3 ${!isOpen && 'justify-center'}`}>
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              {isOpen && (
                <div>
                  <h1 className="text-white font-bold text-lg">RDP Stealth</h1>
                  <p className="text-gray-400 text-xs">v2.1.0</p>
                </div>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggle}
              className="text-gray-400 hover:text-white hover:bg-purple-500/20"
            >
              {isOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                  isActive 
                    ? 'bg-gradient-to-r from-purple-600/20 to-blue-600/20 text-white border border-purple-500/30' 
                    : 'text-gray-400 hover:text-white hover:bg-purple-500/10'
                } ${!isOpen && 'justify-center'}`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-purple-400' : 'group-hover:text-purple-400'} transition-colors`} />
                {isOpen && (
                  <>
                    <span className="font-medium">{item.label}</span>
                    {item.badge && (
                      <span className="ml-auto bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </Link>
            );
          })}
        </nav>

        {/* User Info & Logout */}
        <div className="p-4 border-t border-purple-500/20">
          {isOpen && (
            <div className="mb-3 p-3 bg-purple-500/10 rounded-lg">
              <p className="text-white font-medium text-sm">{user?.username}</p>
              <p className="text-gray-400 text-xs">{user?.role}</p>
              <p className="text-gray-500 text-xs">IP: 127.0.0.1</p>
            </div>
          )}
          
          <Button
            onClick={handleLogout}
            variant="ghost"
            className={`w-full text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-colors ${!isOpen && 'px-2'}`}
          >
            <LogOut className="w-4 h-4" />
            {isOpen && <span className="ml-2">Выйти</span>}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;