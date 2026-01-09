import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Clock, User, Flag, AlertTriangle } from 'lucide-react';
import { toast } from '../hooks/use-toast';
import axios from 'axios';
import './Tarefas.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Tarefas = () => {
  const [projetos, setProjetos] = useState([]);
  const [projetoSelecionado, setProjetoSelecionado] = useState(null);
  const [kanban, setKanban] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    carregarProjetos();
  }, []);

  useEffect(() => {
    if (projetoSelecionado) {
      carregarKanban();
    }
  }, [projetoSelecionado]);

  const carregarProjetos = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/projetos`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjetos(response.data);
      if (response.data.length > 0) {
        setProjetoSelecionado(response.data[0].id);
      }
      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar projetos:', error);
      toast({ title: 'Erro ao carregar projetos', variant: 'destructive' });
      setLoading(false);
    }
  };

  const carregarKanban = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/tarefas/kanban/${projetoSelecionado}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setKanban(response.data);
    } catch (error) {
      console.error('Erro ao carregar kanban:', error);
      toast({ title: 'Erro ao carregar tarefas', variant: 'destructive' });
    }
  };

  const onDragEnd = async (result) => {
    if (!result.destination) return;

    const { source, destination, draggableId } = result;

    // Se soltou na mesma coluna
    if (source.droppableId === destination.droppableId) {
      return;
    }

    // Obter token
    const token = localStorage.getItem('token');
    if (!token) {
      toast({ title: 'Erro', description: 'Token de autenticação não encontrado', variant: 'destructive' });
      return;
    }

    // Mover tarefa entre colunas
    try {
      // Se moveu para CONCLUIDO, atualizar status para Concluído
      if (destination.droppableId === 'CONCLUIDO') {
        await axios.put(`${API}/tarefas/${draggableId}`, {
          status: 'Concluído',
          data_conclusao: new Date().toISOString()
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast({ title: '✅ Tarefa concluída com sucesso!' });
      } else {
        // Mapear coluna para etapa
        const colunaParaEtapa = {
          'LANCAMENTO': '1 - Lançamento do Contrato',
          'ATIVACAO': '2 - Ativação do Projeto',
          'REVISAO': '3 - Revisão de Texto / Preparação das Fotos',
          'CRIACAO_1_2': '4 - Criação (1ª e 2ª AP)',
          'CRIACAO_3_4': '6 - Criação (3ª e 4ª AP)',
          'APROVACAO': '7 - Aprovação Final (Criação)',
          'PLANEJAMENTO': '8 - Planejamento de Produção',
          'PRE_PRODUCAO': '9 - Pré-Produção',
          'PRODUCAO': '10 - Produção'
        };

        const novaEtapa = colunaParaEtapa[destination.droppableId];
        
        await axios.put(`${API}/tarefas/${draggableId}/mover?nova_etapa=${encodeURIComponent(novaEtapa)}`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        toast({ title: '✅ Tarefa movida com sucesso!' });
      }
      
      carregarKanban();
    } catch (error) {
      console.error('Erro ao mover tarefa:', error);
      toast({ 
        title: 'Erro ao mover tarefa', 
        variant: 'destructive',
        description: error.response?.data?.detail || error.message 
      });
    }
  };

  const getStatusBadge = (status) => {
    const config = {
      'Pendente': { className: 'bg-gray-100 text-gray-800' },
      'Em Andamento': { className: 'bg-blue-100 text-blue-800' },
      'Aguardando': { className: 'bg-yellow-100 text-yellow-800' },
      'Concluído': { className: 'bg-green-100 text-green-800' },
      'Atrasado': { className: 'bg-red-100 text-red-800' }
    };
    const cfg = config[status] || config['Pendente'];
    return <Badge className={cfg.className}>{status}</Badge>;
  };

  const calcularDiasRestantes = (prazo) => {
    const agora = new Date();
    const dataPrazo = new Date(prazo);
    const diff = Math.ceil((dataPrazo - agora) / (1000 * 60 * 60 * 24));
    return diff;
  };

  if (loading) {
    return (
      <Layout>
        <div className="loading">Carregando...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="tarefas-page">
        <div className="page-header">
          <div>
            <h1 className="page-title">Kanban de Tarefas</h1>
            <p className="page-subtitle">Arraste as tarefas entre as colunas para atualizar o progresso</p>
          </div>
          <div className="w-64">
            <Select value={projetoSelecionado} onValueChange={setProjetoSelecionado}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione um projeto" />
              </SelectTrigger>
              <SelectContent>
                {projetos.map(p => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.cliente || `Projeto ${p.id.substring(0, 8)}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {kanban && (
          <DragDropContext onDragEnd={onDragEnd}>
            <div className="kanban-container">
              {Object.entries(kanban).map(([key, coluna]) => (
                <div key={key} className="kanban-coluna">
                  <div className="coluna-header" style={{ borderTopColor: coluna.cor }}>
                    <h3 className="coluna-titulo">{coluna.titulo}</h3>
                    <Badge variant="outline" className="coluna-contador">
                      {coluna.tarefas.length}
                    </Badge>
                  </div>

                  <Droppable droppableId={key}>
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.droppableProps}
                        className={`coluna-tarefas ${snapshot.isDraggingOver ? 'dragging-over' : ''}`}
                      >
                        {coluna.tarefas.length === 0 ? (
                          <div className="coluna-vazia">
                            <p>Arraste tarefas aqui</p>
                          </div>
                        ) : (
                          coluna.tarefas.map((tarefa, index) => {
                            const diasRestantes = calcularDiasRestantes(tarefa.prazo);
                            const isCritico = diasRestantes < 0;
                            const isAtencao = diasRestantes <= 3 && diasRestantes >= 0;

                            return (
                              <Draggable key={tarefa.id} draggableId={tarefa.id} index={index}>
                                {(provided, snapshot) => (
                                  <Card
                                    ref={provided.innerRef}
                                    {...provided.draggableProps}
                                    {...provided.dragHandleProps}
                                    className={`tarefa-card ${snapshot.isDragging ? 'dragging' : ''} ${isCritico ? 'border-red-500' : isAtencao ? 'border-yellow-500' : ''}`}
                                  >
                                    <CardHeader className="pb-2">
                                      <div className="flex justify-between items-start gap-2">
                                        <h4 className="text-sm font-semibold flex-1">{tarefa.titulo}</h4>
                                        {tarefa.critica && (
                                          <Badge variant="destructive" className="text-xs">
                                            <Flag size={10} className="mr-1" />
                                            Crítica
                                          </Badge>
                                        )}
                                      </div>
                                    </CardHeader>
                                    <CardContent className="space-y-2">
                                      <div className="flex items-center justify-between text-xs">
                                        <div className="flex items-center gap-1 text-gray-600">
                                          <User size={12} />
                                          <span>{tarefa.responsavel}</span>
                                        </div>
                                        {getStatusBadge(tarefa.status)}
                                      </div>

                                      <div className="flex items-center justify-between text-xs">
                                        <div className="flex items-center gap-1 text-gray-600">
                                          <Clock size={12} />
                                          <span>
                                            {isCritico ? (
                                              <span className="text-red-600 font-bold">
                                                {Math.abs(diasRestantes)} dias atrasada
                                              </span>
                                            ) : isAtencao ? (
                                              <span className="text-yellow-600 font-bold">
                                                {diasRestantes} dias restantes
                                              </span>
                                            ) : (
                                              <span>{diasRestantes} dias</span>
                                            )}
                                          </span>
                                        </div>
                                        <Badge variant="outline" className="text-xs">
                                          {tarefa.setor}
                                        </Badge>
                                      </div>

                                      {isCritico && (
                                        <div className="bg-red-50 border border-red-200 rounded p-1.5 text-xs text-red-700 flex items-center gap-1">
                                          <AlertTriangle size={10} />
                                          <span className="font-medium">ATRASADA!</span>
                                        </div>
                                      )}
                                    </CardContent>
                                  </Card>
                                )}
                              </Draggable>
                            );
                          })
                        )}
                        {provided.placeholder}
                      </div>
                    )}
                  </Droppable>
                </div>
              ))}
            </div>
          </DragDropContext>
        )}
      </div>
    </Layout>
  );
};

export default Tarefas;
