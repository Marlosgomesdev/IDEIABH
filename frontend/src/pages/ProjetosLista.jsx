import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Progress } from '../components/ui/progress';
import { AlertTriangle, TrendingUp, Calendar, User, Filter, FileText, ChevronRight } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import './ProjetosLista.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProjetosLista = () => {
  const [projetos, setProjetos] = useState([]);
  const [projetosFiltrados, setProjetosFiltrados] = useState([]);
  const [projetoSelecionado, setProjetoSelecionado] = useState(null);
  const [showDetalhesModal, setShowDetalhesModal] = useState(false);
  const [filtro, setFiltro] = useState('todos');
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    carregarProjetos();
    // Auto-refresh a cada 30 segundos
    const interval = setInterval(carregarProjetos, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    filtrarProjetos();
  }, [projetos, filtro]);

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

  const filtrarProjetos = () => {
    let filtrados = [...projetos];

    switch (filtro) {
      case 'pre-producao':
        filtrados = projetos.filter(p => p.macro_etapa === 'Pré-Produção' || p.macro_etapa === 'Atendimento' || p.macro_etapa === 'Criação' || p.macro_etapa === 'Preparação');
        break;
      case 'producao':
        filtrados = projetos.filter(p => p.macro_etapa === 'Produção');
        break;
      case 'pos-producao':
        filtrados = projetos.filter(p => p.macro_etapa === 'Pós-Vendas');
        break;
      case 'risco-alto':
        filtrados = projetos.filter(p => p.risco === 'Alto');
        break;
      case 'concluidos':
        filtrados = projetos.filter(p => p.etapa_atual?.includes('Encerrado'));
        break;
      default:
        break;
    }

    setProjetosFiltrados(filtrados);
  };

  const getRiscoBadge = (risco) => {
    const configs = {
      'Alto': { className: 'bg-red-100 text-red-800 border-red-300', label: 'ALTO RISCO' },
      'Médio': { className: 'bg-yellow-100 text-yellow-800 border-yellow-300', label: 'MÉDIO RISCO' },
      'Baixo': { className: 'bg-green-100 text-green-800 border-green-300', label: 'BAIXO RISCO' }
    };

    const config = configs[risco] || configs['Baixo'];

    return (
      <Badge className={config.className}>
        {config.label}
      </Badge>
    );
  };

  const getMacroEtapaBadge = (macroEtapa) => {
    const configs = {
      'Atendimento': { className: 'bg-blue-100 text-blue-800', icon: '📋' },
      'Preparação': { className: 'bg-purple-100 text-purple-800', icon: '📝' },
      'Criação': { className: 'bg-pink-100 text-pink-800', icon: '🎨' },
      'Pré-Produção': { className: 'bg-orange-100 text-orange-800', icon: '📦' },
      'Produção': { className: 'bg-indigo-100 text-indigo-800', icon: '⚙️' },
      'Pós-Vendas': { className: 'bg-green-100 text-green-800', icon: '✅' }
    };

    const config = configs[macroEtapa] || configs['Atendimento'];

    return (
      <Badge className={config.className}>
        {config.icon} {macroEtapa}
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
      return 'Entrega hoje!';
    } else if (diffDias <= 3) {
      return `${diffDias} dias (urgente!)`;
    } else {
      return `${diffDias} dias`;
    }
  };

  const abrirDetalhes = (projeto) => {
    setProjetoSelecionado(projeto);
    setShowDetalhesModal(true);
  };

  const avancarEtapa = async (projetoId) => {
    try {
      const token = getToken();
      await axios.post(`${API}/projetos/${projetoId}/avancar`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast({
        title: '✅ Projeto avançado com sucesso!',
        description: 'O projeto foi movido para a próxima etapa'
      });

      carregarProjetos();
      setShowDetalhesModal(false);
    } catch (error) {
      console.error('Erro ao avançar projeto:', error);
      toast({
        title: 'Erro ao avançar projeto',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive'
      });
    }
  };

  if (loading) {
    return <Layout><div className="loading-container">Carregando projetos...</div></Layout>;
  }

  return (
    <Layout>
      <div className="projetos-lista-container" data-testid="projetos-lista-page">
        <div className="page-header">
          <div>
            <h1 className="page-title">Esteira de Projetos</h1>
            <p className="page-subtitle">Acompanhe o progresso de todos os projetos</p>
          </div>

          <div className="filtros-container">
            <Select value={filtro} onValueChange={setFiltro}>
              <SelectTrigger className="w-[220px]" data-testid="filtro-projetos">
                <Filter size={16} className="mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos os Projetos</SelectItem>
                <SelectItem value="pre-producao">Pré-Produção</SelectItem>
                <SelectItem value="producao">Produção</SelectItem>
                <SelectItem value="pos-producao">Pós-Produção</SelectItem>
                <SelectItem value="risco-alto">Alto Risco</SelectItem>
                <SelectItem value="concluidos">Concluídos</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <Card>
          <CardContent className="p-0">
            <div className="table-container">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Risco</TableHead>
                    <TableHead>Cliente</TableHead>
                    <TableHead>Faculdade</TableHead>
                    <TableHead>Etapa Atual</TableHead>
                    <TableHead>Macro Etapa</TableHead>
                    <TableHead>Progresso</TableHead>
                    <TableHead>Entrega</TableHead>
                    <TableHead>Dias Restantes</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {projetosFiltrados.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8 text-gray-500">
                        Nenhum projeto encontrado
                      </TableCell>
                    </TableRow>
                  ) : (
                    projetosFiltrados.map((projeto) => {
                      const diasRestantes = getDiasRestantes(projeto.data_entrega);
                      const isUrgente = diasRestantes.includes('urgente') || diasRestantes.includes('atraso');
                      
                      return (
                        <TableRow 
                          key={projeto.id}
                          className="cursor-pointer hover:bg-gray-50 transition-colors"
                          onClick={() => abrirDetalhes(projeto)}
                          data-testid={`projeto-row-${projeto.id}`}
                        >
                          <TableCell>
                            {getRiscoBadge(projeto.risco)}
                          </TableCell>
                          <TableCell>
                            <div className="font-medium">{projeto.cliente || 'Cliente não informado'}</div>
                            <div className="text-sm text-gray-500">#{projeto.contrato_numero || 'N/A'}</div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm max-w-xs truncate">{projeto.faculdade || 'N/A'}</div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm font-medium">{projeto.etapa_atual}</div>
                          </TableCell>
                          <TableCell>
                            {getMacroEtapaBadge(projeto.macro_etapa)}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Progress value={projeto.progresso || 0} className="w-24" />
                              <span className="text-sm font-medium">{Math.round(projeto.progresso || 0)}%</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Calendar size={14} className="text-gray-400" />
                              <span className="text-sm">
                                {projeto.data_entrega ? new Date(projeto.data_entrega).toLocaleDateString('pt-BR') : 'N/A'}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <span className={`font-medium text-sm ${isUrgente ? 'text-red-600' : 'text-gray-600'}`}>
                              {diasRestantes}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                abrirDetalhes(projeto);
                              }}
                              data-testid={`ver-detalhes-${projeto.id}`}
                            >
                              Ver Detalhes
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Modal de Detalhes do Projeto */}
        <Dialog open={showDetalhesModal} onOpenChange={setShowDetalhesModal}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Detalhes do Projeto</DialogTitle>
              <DialogDescription>
                Visualize e gerencie os detalhes deste projeto
              </DialogDescription>
            </DialogHeader>

            {projetoSelecionado && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">{projetoSelecionado.cliente}</h3>
                  {getRiscoBadge(projetoSelecionado.risco)}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Faculdade</p>
                    <p className="font-medium">{projetoSelecionado.faculdade || 'N/A'}</p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-500">Contrato</p>
                    <p className="font-medium">#{projetoSelecionado.contrato_numero || 'N/A'}</p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-500">Macro Etapa</p>
                    <div className="mt-1">{getMacroEtapaBadge(projetoSelecionado.macro_etapa)}</div>
                  </div>

                  <div>
                    <p className="text-sm text-gray-500">Etapa Atual</p>
                    <p className="font-medium text-sm mt-1">{projetoSelecionado.etapa_atual}</p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-500">Progresso</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Progress value={projetoSelecionado.progresso || 0} className="flex-1" />
                      <span className="font-medium">{Math.round(projetoSelecionado.progresso || 0)}%</span>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm text-gray-500">Data de Entrega</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Calendar size={16} className="text-gray-400" />
                      <span className="font-medium">
                        {projetoSelecionado.data_entrega ? new Date(projetoSelecionado.data_entrega).toLocaleDateString('pt-BR') : 'N/A'}
                      </span>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm text-gray-500">Responsável Atendimento</p>
                    <div className="flex items-center gap-2 mt-1">
                      <User size={16} className="text-gray-400" />
                      <span>{projetoSelecionado.responsavel_atendimento || 'N/A'}</span>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm text-gray-500">Responsável Designer</p>
                    <div className="flex items-center gap-2 mt-1">
                      <User size={16} className="text-gray-400" />
                      <span>{projetoSelecionado.responsavel_designer || 'N/A'}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-500 mb-2">Tempo Restante</p>
                  <p className={`font-medium ${getDiasRestantes(projetoSelecionado.data_entrega).includes('atraso') ? 'text-red-600' : 'text-gray-700'}`}>
                    {getDiasRestantes(projetoSelecionado.data_entrega)}
                  </p>
                </div>

                {!projetoSelecionado.etapa_atual?.includes('Encerrado') && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <ChevronRight className="text-blue-600 mt-1" size={20} />
                      <div className="flex-1">
                        <h4 className="font-medium text-blue-900 mb-1">Avançar Projeto</h4>
                        <p className="text-sm text-blue-700 mb-3">
                          Mover este projeto para a próxima etapa do fluxo de trabalho.
                        </p>
                        <Button
                          onClick={() => avancarEtapa(projetoSelecionado.id)}
                          className="bg-blue-600 hover:bg-blue-700"
                          data-testid="avancar-projeto-btn"
                        >
                          <ChevronRight size={16} className="mr-2" />
                          Avançar para Próxima Etapa
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                {projetoSelecionado.etapa_atual?.includes('Encerrado') && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                    <FileText className="text-green-600 mx-auto mb-2" size={32} />
                    <p className="font-medium text-green-900">Projeto Concluído</p>
                    <p className="text-sm text-green-700 mt-1">Este projeto foi finalizado com sucesso!</p>
                  </div>
                )}
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowDetalhesModal(false)}>
                Fechar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
};

export default ProjetosLista;
