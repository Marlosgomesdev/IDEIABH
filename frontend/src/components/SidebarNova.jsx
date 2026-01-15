import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Users, Palette, Package, Truck, FileText, DollarSign, UserCircle, Settings, HelpCircle, LogOut } from 'lucide-react';
import './SidebarNova.css';

const SidebarNova = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      try {
        setUser(JSON.parse(userData));
      } catch (e) {
        console.error('Erro ao carregar usuário:', e);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const menuItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', color: '#3b82f6' },
    { path: '/projetos', icon: Package, label: 'Projetos', color: '#8b5cf6' },
    { path: '/tarefas', icon: FileText, label: 'Tarefas', color: '#10b981' },
    { path: '/contratos', icon: FileText, label: 'Contratos', color: '#f59e0b' },
  ];

  // Adicionar Usuários apenas para admin
  if (user && (user.role === 'Administrador' || user.permissoes?.admin)) {
    menuItems.push({ path: '/admin/users', icon: UserCircle, label: 'Usuários', color: '#6366f1' });
  }

  const isActive = (path) => location.pathname === path;

  return (
    <aside className="sidebar-nova">
      {/* Logo */}
      <div className="sidebar-header">
        <div className="logo-container">
          <div className="logo-icon">IB</div>
          <div className="logo-text">
            <div className="logo-title">IdeiaBH</div>
            <div className="logo-subtitle">Gestão de Processos</div>
          </div>
        </div>
      </div>

      {/* Menu Items */}
      <nav className="sidebar-menu">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`menu-item ${active ? 'active' : ''}`}
              style={active ? { backgroundColor: 'rgba(59, 130, 246, 0.1)' } : {}}
            >
              <Icon 
                className="menu-icon" 
                size={20} 
                style={{ color: active ? item.color : '#64748b' }}
              />
              <span className="menu-label" style={{ color: active ? item.color : '#334155' }}>
                {item.label}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className="sidebar-bottom">
        <div className="user-info">
          <div className="user-avatar">
            {user?.nome?.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}
          </div>
          <div className="user-details">
            <div className="user-name">{user?.nome || 'Usuário'}</div>
            <div className="user-role">{user?.role || 'Operador'}</div>
          </div>
        </div>
        <button className="logout-btn" onClick={handleLogout} title="Sair">
          <LogOut size={18} />
        </button>
      </div>
    </aside>
  );
};

export default SidebarNova;