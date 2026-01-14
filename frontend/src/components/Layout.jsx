import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, FileText, FolderKanban, CheckSquare, LogOut, Users } from 'lucide-react';
import Notificacoes from './Notificacoes';
import './Layout.css';

const Layout = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [menuItems, setMenuItems] = useState([]);

  useEffect(() => {
    // Carregar dados do usuário
    const userData = localStorage.getItem('user');
    if (userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        
        // Construir menu baseado em permissões
        const items = [];
        const perms = parsedUser.permissoes || {};
        
        // Dashboard sempre visível se tiver permissão
        if (perms.dashboard) {
          items.push({ path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' });
        }
        
        // Contratos
        if (perms.contratos_visualizar) {
          items.push({ path: '/contratos', icon: FileText, label: 'Contratos' });
        }
        
        // Projetos
        if (perms.projetos_visualizar) {
          items.push({ path: '/projetos', icon: FolderKanban, label: 'Projetos' });
        }
        
        // Tarefas
        if (perms.tarefas_visualizar) {
          items.push({ path: '/tarefas', icon: CheckSquare, label: 'Tarefas' });
        }
        
        // Usuários (apenas admin)
        if (perms.admin || parsedUser.role === 'Administrador') {
          items.push({ path: '/admin/users', icon: Users, label: 'Usuários' });
        }
        
        setMenuItems(items);
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
        <div className="top-bar">
          <div className="top-bar-left">
            {user && <span className="user-name">Olá, {user.nome}</span>}
          </div>
          <div className="top-bar-right">
            <Notificacoes />
          </div>
        </div>
        <div className="content-wrapper">{children}</div>
      </main>
    </div>
  );
};

export default Layout;