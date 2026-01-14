import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Clock, AlertTriangle, CheckCircle2, User, Calendar, FileText, Filter } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import './TarefasLista.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TarefasLista = () => {
  const [tarefas, setTarefas] = useState([]);
  const [tarefasFiltradas, setTarefasFiltradas] = useState([]);
  const [tarefaSelecionada, setTarefaSelecionada] = useState(null);
  const [showDetalhesModal, setShowDetalhesModal] = useState(false);
  const [observacao, setObservacao] = useState('');
  const [filtro, setFiltro] = useState('todas');
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    carregarTarefas();
    // Auto-refresh a cada 30 segundos
    const interval = setInterval(carregarTarefas, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    filtrarTarefas();
  }, [tarefas, filtro]);

  const getToken = () => localStorage.getItem('token');
  const getUser = () => JSON.parse(localStorage.getItem('user') || '{}');

  const carregarTarefas = async () => {
    try {
      const token = getToken();
      const response = await axios.get(`${API}/tarefas`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTarefas(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar tarefas:', error);
      toast({
        title: 'Erro ao carregar tarefas',
        variant: 'destructive'
      });
      setLoading(false);
    }
  };

  const filtrarTarefas = () => {
    const user = getUser();
    let filtradas = [...tarefas];

    switch (filtro) {
      case 'minhas':
        filtradas = tarefas.filter(t => t.responsavel === user.nome);
        break;
      case 'atrasadas':
        filtradas = tarefas.filter(t => calcularStatus(t.prazo, t.status) === 'atrasada');
        break;
      case 'proximas':
        filtradas = tarefas.filter(t => calcularStatus(t.prazo, t.status) === 'proxima');
        break;
      case 'concluidas':
        filtradas = tarefas.filter(t => t.status === 'Concluído');
        break;
      default:
        break;
    }

    setTarefasFiltradas(filtradas);
  };

  const calcularStatus = (prazo, statusTarefa) => {
    if (statusTarefa === 'Concluído') return 'concluida';
    
    const agora = new Date();
    const dataPrazo = new Date(prazo);
    const diffDias = Math.ceil((dataPrazo - agora) / (1000 * 60 * 60 * 24));

    if (diffDias < 0) return 'atrasada';
    if (diffDias <= 1) return 'proxima';
    return 'normal';
  };

  const getStatusBadge = (prazo, status) => {
    const statusCalc = calcularStatus(prazo, status);

    const configs = {
      atrasada: { className: 'bg-red-100 text-red-800 border-red-300', label: 'ATRASADA', icon: AlertTriangle },
      proxima: { className: 'bg-yellow-100 text-yellow-800 border-yellow-300', label: 'VENCE EM BREVE', icon: Clock },
      normal: { className: 'bg-blue-100 text-blue-800 border-blue-300', label: 'NO PRAZO', icon: Clock },
      concluida: { className: 'bg-green-100 text-green-800 border-green-300', label: 'CONCLUÍDA', icon: CheckCircle2 }
    };

    const config = configs[statusCalc];
    const Icon = config.icon;

    return (
      <Badge className={`${config.className} flex items-center gap-1`}>
        <Icon size={12} />
        {config.label}
      </Badge>
    );
  };

  const getDiasRestantes = (prazo) => {
    const agora = new Date();
    const dataPrazo = new Date(prazo);
    const diffDias = Math.ceil((dataPrazo - agora) / (1000 * 60 * 60 * 24));

    if (diffDias < 0) {
      return `${Math.abs(diffDias)} dias de atraso`;
    } else if (diffDias === 0) {
      return 'Vence hoje!';
    } else if (diffDias === 1) {
      return 'Vence amanhã!';
    } else {
      return `${diffDias} dias restantes`;
    }
  };

  const abrirDetalhes = (tarefa) => {
    setTarefaSelecionada(tarefa);
    setObservacao(tarefa.observacao || '');
    setShowDetalhesModal(true);
  };

  const concluirTarefa = async () => {
    if (!tarefaSelecionada) return;

    const statusTarefa = calcularStatus(tarefaSelecionada.prazo, tarefaSelecionada.status);
    
    // Se está atrasada, obrigar observação
    if (statusTarefa === 'atrasada' && !observacao.trim()) {
      toast({
        title: 'Observação obrigatória',
        description: 'Por favor, justifique o motivo do atraso',
        variant: 'destructive'
      });
      return;
    }

    try {
      const token = getToken();
      await axios.put(`${API}/tarefas/${tarefaSelecionada.id}`, {
        status: 'Concluído',
        data_conclusao: new Date().toISOString(),
        observacao: observacao
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast({
        title: '✅ Tarefa concluída com sucesso!',
        description: 'A tarefa foi marcada como concluída'
      });

      setShowDetalhesModal(false);
      setTarefaSelecionada(null);
      setObservacao('');
      carregarTarefas();
    } catch (error) {
      console.error('Erro ao concluir tarefa:', error);
      toast({
        title: 'Erro ao concluir tarefa',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive'
      });
    }
  };

  const salvarObservacao = async () => {
    if (!tarefaSelecionada) return;

    try {
      const token = getToken();
      await axios.put(`${API}/tarefas/${tarefaSelecionada.id}`, {
        observacao: observacao
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast({
        title: '✅ Observação salva',
        description: 'A observação foi salva com sucesso'
      });

      carregarTarefas();
    } catch (error) {
      console.error('Erro ao salvar observação:', error);
      toast({
        title: 'Erro ao salvar observação',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive'
      });
    }
  };

  if (loading) {
    return <Layout><div className="loading-container">Carregando tarefas...</div></Layout>;
  }

  return (
    <Layout>
      <div className="tarefas-lista-container" data-testid="tarefas-lista-page">
        <div className="page-header">
          <div>
            <h1 className="page-title">Minhas Tarefas</h1>
            <p className="page-subtitle">Gerencie suas tarefas e prazos</p>
          </div>

          <div className="filtros-container">
            <Select value={filtro} onValueChange={setFiltro}>
              <SelectTrigger className="w-[200px]" data-testid="filtro-tarefas">
                <Filter size={16} className="mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todas">Todas as Tarefas</SelectItem>
                <SelectItem value="minhas">Minhas Tarefas</SelectItem>
                <SelectItem value="atrasadas">Atrasadas</SelectItem>
                <SelectItem value="proximas">Próximas a Vencer</SelectItem>
                <SelectItem value="concluidas">Concluídas</SelectItem>
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
                    <TableHead>Status</TableHead>
                    <TableHead>Tarefa</TableHead>
                    <TableHead>Responsável</TableHead>
                    <TableHead>Prazo</TableHead>
                    <TableHead>Dias Restantes</TableHead>
                    <TableHead>Etapa</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tarefasFiltradas.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                        Nenhuma tarefa encontrada
                      </TableCell>
                    </TableRow>
                  ) : (
                    tarefasFiltradas.map((tarefa) => (
                      <TableRow 
                        key={tarefa.id}
                        className="cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => abrirDetalhes(tarefa)}
                        data-testid={`tarefa-row-${tarefa.id}`}
                      >
                        <TableCell>
                          {getStatusBadge(tarefa.prazo, tarefa.status)}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-start gap-2">
                            {tarefa.critica && (
                              <AlertTriangle size={16} className="text-red-500 mt-1" />
                            )}
                            <div>
                              <div className="font-medium">{tarefa.titulo}</div>
                              {tarefa.descricao && (
                                <div className="text-sm text-gray-500 truncate max-w-xs">
                                  {tarefa.descricao}
                                </div>
                              )}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <User size={14} className="text-gray-400" />
                            <span>{tarefa.responsavel}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Calendar size={14} className="text-gray-400" />
                            <span>{new Date(tarefa.prazo).toLocaleDateString('pt-BR')}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className={`font-medium ${calcularStatus(tarefa.prazo, tarefa.status) === 'atrasada' ? 'text-red-600' : calcularStatus(tarefa.prazo, tarefa.status) === 'proxima' ? 'text-yellow-600' : 'text-gray-600'}`}>
                            {getDiasRestantes(tarefa.prazo)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{tarefa.setor}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              abrirDetalhes(tarefa);
                            }}
                            data-testid={`ver-detalhes-${tarefa.id}`}
                          >
                            Ver Detalhes
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Modal de Detalhes da Tarefa */}
        <Dialog open={showDetalhesModal} onOpenChange={setShowDetalhesModal}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Detalhes da Tarefa</DialogTitle>
              <DialogDescription>
                Visualize e gerencie os detalhes desta tarefa
              </DialogDescription>
            </DialogHeader>

            {tarefaSelecionada && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">{tarefaSelecionada.titulo}</h3>
                  {getStatusBadge(tarefaSelecionada.prazo, tarefaSelecionada.status)}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm text-gray-500">Responsável</Label>
                    <div className="flex items-center gap-2 mt-1">
                      <User size={16} className="text-gray-400" />
                      <span className="font-medium">{tarefaSelecionada.responsavel}</span>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm text-gray-500">Prazo</Label>
                    <div className="flex items-center gap-2 mt-1">
                      <Calendar size={16} className="text-gray-400" />
                      <span className="font-medium">
                        {new Date(tarefaSelecionada.prazo).toLocaleDateString('pt-BR')}
                      </span>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm text-gray-500">Etapa</Label>
                    <div className="mt-1">
                      <Badge variant="outline">{tarefaSelecionada.etapa}</Badge>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm text-gray-500">Setor</Label>
                    <div className="mt-1">
                      <Badge>{tarefaSelecionada.setor}</Badge>
                    </div>
                  </div>
                </div>

                {tarefaSelecionada.descricao && (
                  <div>
                    <Label className="text-sm text-gray-500">Descrição</Label>
                    <p className="mt-1 text-sm">{tarefaSelecionada.descricao}</p>
                  </div>
                )}

                <div>
                  <Label className="text-sm text-gray-500">Tempo Restante</Label>
                  <p className={`mt-1 font-medium ${calcularStatus(tarefaSelecionada.prazo, tarefaSelecionada.status) === 'atrasada' ? 'text-red-600' : 'text-gray-700'}`}>
                    {getDiasRestantes(tarefaSelecionada.prazo)}
                  </p>
                </div>

                <div>
                  <Label htmlFor="observacao">
                    Observações {calcularStatus(tarefaSelecionada.prazo, tarefaSelecionada.status) === 'atrasada' && (
                      <span className="text-red-600">* (Obrigatório para tarefas atrasadas)</span>
                    )}
                  </Label>
                  <Textarea
                    id="observacao"
                    value={observacao}
                    onChange={(e) => setObservacao(e.target.value)}
                    placeholder="Digite suas observações sobre esta tarefa..."
                    rows={4}
                    className="mt-1"
                    data-testid="observacao-input"
                  />
                  {observacao !== (tarefaSelecionada.observacao || '') && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={salvarObservacao}
                      className="mt-2"
                    >
                      Salvar Observação
                    </Button>
                  )}
                </div>

                {tarefaSelecionada.status !== 'Concluído' && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <FileText className="text-blue-600 mt-1" size={20} />
                      <div className="flex-1">
                        <h4 className="font-medium text-blue-900 mb-1">Concluir Tarefa</h4>
                        <p className="text-sm text-blue-700 mb-3">
                          Ao concluir esta tarefa, ela será marcada como finalizada e a próxima etapa será notificada.
                          {calcularStatus(tarefaSelecionada.prazo, tarefaSelecionada.status) === 'atrasada' && (
                            <span className="block mt-1 font-medium">
                              ⚠️ Esta tarefa está atrasada. É obrigatório justificar o atraso no campo de observações.
                            </span>
                          )}
                        </p>
                        <Button
                          onClick={concluirTarefa}
                          className="bg-green-600 hover:bg-green-700"
                          data-testid="concluir-tarefa-btn"
                        >
                          <CheckCircle2 size={16} className="mr-2" />
                          Concluir Tarefa
                        </Button>
                      </div>
                    </div>
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

export default TarefasLista;
