import React, { useState, useEffect } from 'react';
import axios from 'axios';
import LayoutNovo from '../components/LayoutNovo';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Calendar, Clock, AlertTriangle, CheckCircle, ChevronRight, User } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import './ProjetosVisaoGeral.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProjetosVisaoGeral = () => {
  const [projetos, setProjetos] = useState([]);
  const [projetoSelecionado, setProjetoSelecionado] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    carregarProjetos();
    const interval = setInterval(carregarProjetos, 30000);
    return () => clearInterval(interval);
  }, []);

  const getToken = () => localStorage.getItem('token');

  const carregarProjetos = async () => {
    try {
      const token = getToken();
      const response = await axios.get(`${API}/projetos`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjetos(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar projetos:', error);
      toast({
        title: 'Erro ao carregar projetos',
        variant: 'destructive'
      });
      setLoading(false);
    }
  };

  const calcularStatusProjeto = (projeto) => {
    if (!projeto.data_entrega) return 'em-andamento';
    
    const agora = new Date();
    const dataEntrega = new Date(projeto.data_entrega);
    const diffDias = Math.ceil((dataEntrega - agora) / (1000 * 60 * 60 * 24));

    if (projeto.etapa_atual?.includes('Encerrado')) return 'concluido';
    if (diffDias < 0) return 'atrasado';
    if (diffDias <= 3) return 'proximo-prazo';
    return 'em-andamento';
  };

  const getStatusBadge = (status) => {
    const configs = {
      'atrasado': { 
        label: 'Atrasado', 
        className: 'badge-atrasado',
        icon: AlertTriangle 
      },
      'proximo-prazo': { 
        label: 'Próximo ao Prazo', 
        className: 'badge-proximo',
        icon: Clock 
      },
      'em-andamento': { 
        label: 'Em Andamento', 
        className: 'badge-andamento',
        icon: Clock 
      },
      'concluido': { 
        label: 'Concluído', 
        className: 'badge-concluido',
        icon: CheckCircle 
      }
    };

    const config = configs[status] || configs['em-andamento'];
    const Icon = config.icon;

    return (
      <Badge className={`status-badge ${config.className}`}>
        <Icon size={14} />
        {config.label}
      </Badge>
    );
  };

  const getDiasRestantes = (dataEntrega) => {
    if (!dataEntrega) return 'Não definido';
    
    const agora = new Date();
    const dataFim = new Date(dataEntrega);
    const diffDias = Math.ceil((dataFim - agora) / (1000 * 60 * 60 * 24));

    if (diffDias < 0) {
      return `${Math.abs(diffDias)} dias de atraso`;
    } else if (diffDias === 0) {
      return 'Entrega hoje';
    } else {
      return `${diffDias} dias restantes`;
    }
  };

  const abrirDetalhes = (projeto) => {
    setProjetoSelecionado(projeto);
    setShowModal(true);
  };

  // Agrupar projetos por status
  const projetosAgrupados = {
    atrasados: projetos.filter(p => calcularStatusProjeto(p) === 'atrasado'),
    proximos: projetos.filter(p => calcularStatusProjeto(p) === 'proximo-prazo'),
    andamento: projetos.filter(p => calcularStatusProjeto(p) === 'em-andamento'),
    concluidos: projetos.filter(p => calcularStatusProjeto(p) === 'concluido')
  };

  if (loading) {
    return <LayoutNovo><div className="loading-container">Carregando projetos...</div></LayoutNovo>;
  }

  return (
    <LayoutNovo>
      <div className="projetos-visao-geral">
        {/* Header */}
        <div className="page-header-novo">
          <div>
            <h1 className="page-title-novo">Projetos</h1>
            <p className="page-subtitle-novo">Visão geral de todos os projetos e seus status</p>
          </div>
        </div>

        {/* KPIs Rápidos */}
        <div className="kpis-grid">
          <div className="kpi-card kpi-atrasados">
            <div className="kpi-icon">
              <AlertTriangle size={24} />
            </div>
            <div className="kpi-content">
              <div className="kpi-value">{projetosAgrupados.atrasados.length}</div>
              <div className="kpi-label">Projetos Atrasados</div>
            </div>
          </div>

          <div className="kpi-card kpi-proximos">
            <div className="kpi-icon">
              <Clock size={24} />
            </div>
            <div className="kpi-content">
              <div className="kpi-value">{projetosAgrupados.proximos.length}</div>
              <div className="kpi-label">Próximos ao Prazo</div>
            </div>
          </div>

          <div className="kpi-card kpi-andamento">
            <div className="kpi-icon">
              <Clock size={24} />
            </div>
            <div className="kpi-content">
              <div className="kpi-value">{projetosAgrupados.andamento.length}</div>
              <div className="kpi-label">Em Andamento</div>
            </div>
          </div>

          <div className="kpi-card kpi-concluidos">
            <div className="kpi-icon">
              <CheckCircle size={24} />
            </div>
            <div className="kpi-content">
              <div className="kpi-value">{projetosAgrupados.concluidos.length}</div>
              <div className="kpi-label">Concluídos</div>
            </div>
          </div>
        </div>

        {/* Projetos Atrasados (Destaque) */}
        {projetosAgrupados.atrasados.length > 0 && (
          <div className="section">
            <h2 className="section-title">
              <AlertTriangle size={20} className="text-red-500" />
              Projetos Atrasados
            </h2>
            <div className="projetos-grid">
              {projetosAgrupados.atrasados.map(projeto => (
                <Card 
                  key={projeto.id} 
                  className="projeto-card projeto-atrasado"
                  onClick={() => abrirDetalhes(projeto)}
                >
                  <CardContent className="p-5">
                    <div className="card-header">
                      <div className="card-title-section">
                        <h3 className="card-title">{projeto.cliente || 'Cliente'}</h3>
                        <p className="card-subtitle">{projeto.faculdade || 'Instituição'}</p>
                      </div>
                      {getStatusBadge(calcularStatusProjeto(projeto))}
                    </div>

                    <div className="card-info">
                      <div className="info-row">
                        <Calendar size={16} className="info-icon" />
                        <span className="info-text">
                          Contrato: #{projeto.contrato_numero || 'N/A'}
                        </span>
                      </div>
                      <div className="info-row">
                        <User size={16} className="info-icon" />
                        <span className="info-text">
                          {projeto.responsavel_atendimento || 'Não atribuído'}
                        </span>
                      </div>
                    </div>

                    <div className="etapa-section">
                      <div className="etapa-label">Etapa atual:</div>
                      <div className="etapa-nome">{projeto.etapa_atual}</div>
                    </div>

                    <div className="progress-section">
                      <div className="progress-header">
                        <span className="progress-label">Progresso</span>
                        <span className="progress-value">{Math.round(projeto.progresso || 0)}%</span>
                      </div>
                      <Progress value={projeto.progresso || 0} className=\"progress-bar\" />
                    </div>

                    <div className="card-footer">
                      <div className="prazo-info atrasado">
                        <Clock size={14} />
                        <span>{getDiasRestantes(projeto.data_entrega)}</span>
                      </div>
                      <ChevronRight size={20} className="arrow-icon" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Todos os Projetos */}
        <div className="section">
          <h2 className="section-title">Todos os Projetos</h2>
          <div className="projetos-grid">
            {projetos.map(projeto => {
              const status = calcularStatusProjeto(projeto);
              return (
                <Card 
                  key={projeto.id} 
                  className={`projeto-card projeto-${status}`}
                  onClick={() => abrirDetalhes(projeto)}
                >
                  <CardContent className="p-5">
                    <div className="card-header">
                      <div className="card-title-section">
                        <h3 className="card-title">{projeto.cliente || 'Cliente'}</h3>
                        <p className="card-subtitle">{projeto.faculdade || 'Instituição'}</p>
                      </div>
                      {getStatusBadge(status)}
                    </div>

                    <div className="card-info">
                      <div className="info-row">
                        <Calendar size={16} className="info-icon" />
                        <span className="info-text">
                          Contrato: #{projeto.contrato_numero || 'N/A'}
                        </span>
                      </div>
                      <div className="info-row">
                        <User size={16} className="info-icon" />
                        <span className="info-text">
                          {projeto.responsavel_atendimento || 'Não atribuído'}
                        </span>
                      </div>
                    </div>

                    <div className="etapa-section">
                      <div className="etapa-label">Etapa atual:</div>
                      <div className="etapa-nome">{projeto.etapa_atual}</div>
                    </div>

                    <div className="progress-section">
                      <div className="progress-header">
                        <span className="progress-label">Progresso</span>
                        <span className="progress-value">{Math.round(projeto.progresso || 0)}%</span>
                      </div>
                      <Progress value={projeto.progresso || 0} className="progress-bar" />
                    </div>

                    <div className="card-footer">
                      <div className={`prazo-info ${status === 'atrasado' ? 'atrasado' : ''}`}>
                        <Clock size={14} />
                        <span>{getDiasRestantes(projeto.data_entrega)}</span>
                      </div>
                      <ChevronRight size={20} className="arrow-icon" />
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Modal de Detalhes (Temporário - será expandido na Fase 2) */}
        <Dialog open={showModal} onOpenChange={setShowModal}>
          <DialogContent className="max-w-4xl">
            <DialogHeader>
              <DialogTitle>Detalhes do Projeto</DialogTitle>
            </DialogHeader>
            {projetoSelecionado && (
              <div className="p-4">
                <h3 className="text-xl font-semibold mb-4">
                  {projetoSelecionado.cliente}
                </h3>
                <p className="text-gray-600">
                  Detalhamento completo com timeline de etapas será implementado na Fase 2
                </p>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </LayoutNovo>
  );
};

export default ProjetosVisaoGeral;
