import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, FileText, FolderKanban, CheckSquare, LogOut, Users } from 'lucide-react';
import './Layout.css';

const Layout = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    // Verificar se usuário é admin
    const userData = localStorage.getItem('user');
    if (userData) {
      try {
        const user = JSON.parse(userData);
        setIsAdmin(user.role === 'Administrador' || user.permissoes?.admin);
      } catch (e) {
        console.error('Erro ao verificar permissões:', e);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const menuItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/contratos', icon: FileText, label: 'Contratos' },
    { path: '/projetos', icon: FolderKanban, label: 'Projetos' },
    { path: '/tarefas', icon: CheckSquare, label: 'Tarefas' },
  ];

  if (isAdmin) {
    menuItems.push({ path: '/admin/users', icon: Users, label: 'Usuários' });
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2 className="sidebar-logo">IDEIABH</h2>
          <p className="sidebar-subtitle">Sistema de Gestão</p>
        </div>

        <nav className="sidebar-nav">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`nav-item ${isActive ? 'active' : ''}`}
              >
                <Icon className="nav-icon" size={20} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <button className="logout-button" onClick={handleLogout}>
          <LogOut size={20} />
          <span>Sair</span>
        </button>
      </aside>

      <main className="main-content">
        <div className="content-wrapper">{children}</div>
      </main>
    </div>
  );
};

export default Layout;