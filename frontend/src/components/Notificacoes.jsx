import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Bell } from 'lucide-react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from './ui/dropdown-menu';
import { ScrollArea } from './ui/scroll-area';
import { useNavigate } from 'react-router-dom';
import './Notificacoes.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Notificacoes = () => {
  const [notificacoes, setNotificacoes] = useState([]);
  const [naoLidas, setNaoLidas] = useState(0);
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    carregarNotificacoes();
    // Auto-refresh a cada 30 segundos
    const interval = setInterval(carregarNotificacoes, 30000);
    return () => clearInterval(interval);
  }, []);

  const getToken = () => localStorage.getItem('token');

  const carregarNotificacoes = async () => {
    try {
      const token = getToken();
      
      // Buscar contagem de não lidas
      const countResponse = await axios.get(`${API}/notificacoes/nao-lidas`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNaoLidas(countResponse.data.count);

      // Buscar notificações
      const response = await axios.get(`${API}/notificacoes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotificacoes(response.data);
    } catch (error) {
      console.error('Erro ao carregar notificações:', error);
    }
  };

  const marcarComoLida = async (notificacaoId) => {
    try {
      const token = getToken();
      await axios.put(`${API}/notificacoes/${notificacaoId}/ler`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      carregarNotificacoes();
    } catch (error) {
      console.error('Erro ao marcar como lida:', error);
    }
  };

  const marcarTodasComoLidas = async () => {
    try {
      const token = getToken();
      await axios.put(`${API}/notificacoes/ler-todas`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      carregarNotificacoes();
    } catch (error) {
      console.error('Erro ao marcar todas como lidas:', error);
    }
  };

  const handleNotificacaoClick = (notificacao) => {
    marcarComoLida(notificacao.id);
    if (notificacao.tarefa_id) {
      navigate('/tarefas');
    }
    setOpen(false);
  };

  const getIconeNotificacao = (tipo) => {
    const icones = {
      'Nova Tarefa': '📋',
      'Prazo Próximo': '⏰',
      'Tarefa Atrasada': '🔴',
      'Tarefa Concluída': '✅',
      'Tarefa Movida': '➡️'
    };
    return icones[tipo] || '📢';
  };

  const formatarTempo = (data) => {
    const agora = new Date();
    const dataNotif = new Date(data);
    const diffMs = agora - dataNotif;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHoras = Math.floor(diffMins / 60);
    const diffDias = Math.floor(diffHoras / 24);

    if (diffMins < 1) return 'Agora';
    if (diffMins < 60) return `${diffMins}m atrás`;
    if (diffHoras < 24) return `${diffHoras}h atrás`;
    if (diffDias === 1) return 'Ontem';
    if (diffDias < 7) return `${diffDias}d atrás`;
    return dataNotif.toLocaleDateString('pt-BR');
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon" 
          className="relative"
          data-testid="notificacoes-btn"
        >
          <Bell size={20} />
          {naoLidas > 0 && (
            <Badge 
              className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 bg-red-500 text-white text-xs"
              data-testid="notificacoes-badge"
            >
              {naoLidas > 9 ? '9+' : naoLidas}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="end" className="w-[380px]">
        <div className="flex items-center justify-between px-4 py-2 border-b">
          <h3 className="font-semibold">Notificações</h3>
          {naoLidas > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={marcarTodasComoLidas}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Marcar todas como lidas
            </Button>
          )}
        </div>

        <ScrollArea className="h-[400px]">
          {notificacoes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-gray-500">
              <Bell size={48} className="mb-2 opacity-50" />
              <p>Nenhuma notificação</p>
            </div>
          ) : (
            notificacoes.map((notif) => (
              <DropdownMenuItem
                key={notif.id}
                className={`px-4 py-3 cursor-pointer ${!notif.lida ? 'bg-blue-50' : ''}`}
                onClick={() => handleNotificacaoClick(notif)}
                data-testid={`notificacao-${notif.id}`}
              >
                <div className="flex gap-3 w-full">
                  <div className="text-2xl flex-shrink-0">
                    {getIconeNotificacao(notif.tipo)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className={`text-sm ${!notif.lida ? 'font-semibold' : 'font-medium'}`}>
                        {notif.titulo}
                      </p>
                      {!notif.lida && (
                        <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-1" />
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                      {notif.mensagem}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {formatarTempo(notif.created_at)}
                    </p>
                  </div>
                </div>
              </DropdownMenuItem>
            ))
          )}
        </ScrollArea>

        {notificacoes.length > 0 && (
          <>
            <DropdownMenuSeparator />
            <div className="px-4 py-2 text-center">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  navigate('/tarefas');
                  setOpen(false);
                }}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Ver todas as tarefas
              </Button>
            </div>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default Notificacoes;
