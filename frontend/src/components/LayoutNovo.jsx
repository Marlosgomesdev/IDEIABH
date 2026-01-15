import React from 'react';
import SidebarNova from './SidebarNova';
import Notificacoes from './Notificacoes';
import { Search, Share2 } from 'lucide-react';
import './LayoutNovo.css';

const LayoutNovo = ({ children }) => {
  return (
    <div className="layout-novo">
      <SidebarNova />
      
      <div className="main-wrapper">
        {/* Top Bar */}
        <div className="top-bar-novo">
          <div className="search-container">
            <Search size={18} className="search-icon" />
            <input 
              type="text" 
              placeholder="Buscar clientes, contratos..." 
              className="search-input"
            />
          </div>
          
          <div className="top-bar-actions">
            <Notificacoes />
            <button className="icon-btn" title="Compartilhar">
              <Share2 size={18} />
            </button>
          </div>
        </div>
        
        {/* Content */}
        <main className="content-novo">
          {children}
        </main>
      </div>
    </div>
  );
};

export default LayoutNovo;