import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Calendar, DollarSign, User, Building2, Filter, Plus, CheckCircle2, XCircle, Edit, Trash2 } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import './ContratosLista.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ContratosLista = () => {
  const [contratos, setContratos] = useState([]);
  const [contratosFiltrados, setContratosFiltrados] = useState([]);
  const [contratoSelecionado, setContratoSelecionado] = useState(null);
  const [showDetalhesModal, setShowDetalhesModal] = useState(false);
  const [showNovoModal, setShowNovoModal] = useState(false);
  const [filtro, setFiltro] = useState('todos');
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  const [novoContrato, setNovoContrato] = useState({
    cliente: '',
    faculdade: '',
    semestre: '',
    valor: '',
    data_inicio: '',
    data_fim: ''
  });

  useEffect(() => {
    carregarContratos();
    const interval = setInterval(carregarContratos, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    filtrarContratos();
  }, [contratos, filtro]);

  const getToken = () => localStorage.getItem('token');

  const carregarContratos = async () => {
    try {
      const token = getToken();
      const response = await axios.get(`${API}/contratos`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setContratos(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar contratos:', error);
      toast({
        title: 'Erro ao carregar contratos',
        variant: 'destructive'
      });
      setLoading(false);
    }
  };

  const filtrarContratos = () => {
    let filtrados = [...contratos];

    switch (filtro) {
      case 'ativos':
        filtrados = contratos.filter(c => c.status === 'Ativo');
        break;
      case 'em-andamento':
        filtrados = contratos.filter(c => c.status === 'Em Andamento');
        break;
      case 'finalizados':
        filtrados = contratos.filter(c => c.status === 'Finalizado');
        break;
      default:
        break;
    }

    setContratosFiltrados(filtrados);
  };

  const getStatusBadge = (status) => {
    const configs = {
      'Ativo': { className: 'bg-blue-100 text-blue-800 border-blue-300', icon: '🔵' },
      'Em Andamento': { className: 'bg-yellow-100 text-yellow-800 border-yellow-300', icon: '🟡' },
      'Finalizado': { className: 'bg-green-100 text-green-800 border-green-300', icon: '🟢' },
      'Encerrado': { className: 'bg-gray-100 text-gray-800 border-gray-300', icon: '⚫' }
    };

    const config = configs[status] || configs['Ativo'];

    return (
      <Badge className={config.className}>
        {config.icon} {status}
      </Badge>
    );
  };

  const formatarValor = (valor) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(valor);
  };

  const abrirDetalhes = (contrato) => {
    setContratoSelecionado(contrato);
    setShowDetalhesModal(true);
  };

  const criarContrato = async () => {
    try {
      const token = getToken();
      await axios.post(`${API}/contratos`, novoContrato, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast({
        title: '✅ Contrato criado com sucesso!',
        description: 'O novo contrato foi adicionado ao sistema'
      });

      setShowNovoModal(false);
      setNovoContrato({
        cliente: '',
        faculdade: '',
        semestre: '',
        valor: '',
        data_inicio: '',
        data_fim: ''
      });
      carregarContratos();
    } catch (error) {
      console.error('Erro ao criar contrato:', error);
      toast({
        title: 'Erro ao criar contrato',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive'
      });
    }
  };

  const aprovarContrato = async (contratoId) => {
    try {
      const token = getToken();
      await axios.put(`${API}/contratos/${contratoId}/aprovar`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast({
        title: '✅ Contrato aprovado!',
        description: 'O contrato foi aprovado e está em andamento'
      });

      carregarContratos();
      setShowDetalhesModal(false);
    } catch (error) {
      console.error('Erro ao aprovar contrato:', error);
      toast({
        title: 'Erro ao aprovar contrato',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive'
      });
    }
  };

  const finalizarContrato = async (contratoId) => {
    try {
      const token = getToken();
      await axios.put(`${API}/contratos/${contratoId}/finalizar`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast({
        title: '✅ Contrato finalizado!',
        description: 'O contrato foi marcado como finalizado'
      });

      carregarContratos();
      setShowDetalhesModal(false);
    } catch (error) {
      console.error('Erro ao finalizar contrato:', error);
      toast({
        title: 'Erro ao finalizar contrato',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive'
      });
    }
  };

  if (loading) {
    return <Layout><div className="loading-container">Carregando contratos...</div></Layout>;
  }

  return (
    <Layout>
      <div className="contratos-lista-container" data-testid="contratos-lista-page">
        <div className="page-header">
          <div>
            <h1 className="page-title">Contratos</h1>
            <p className="page-subtitle">Gerencie todos os contratos do sistema</p>
          </div>

          <div className="header-actions">
            <Select value={filtro} onValueChange={setFiltro}>
              <SelectTrigger className="w-[200px]" data-testid="filtro-contratos">
                <Filter size={16} className="mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos os Contratos</SelectItem>
                <SelectItem value="ativos">Ativos</SelectItem>
                <SelectItem value="em-andamento">Em Andamento</SelectItem>
                <SelectItem value="finalizados">Finalizados</SelectItem>
              </SelectContent>
            </Select>

            <Button onClick={() => setShowNovoModal(true)} data-testid="novo-contrato-btn">
              <Plus size={18} className="mr-2" />
              Novo Contrato
            </Button>
          </div>
        </div>

        <Card>
          <CardContent className="p-0">
            <div className="table-container">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Status</TableHead>
                    <TableHead>Nº Contrato</TableHead>
                    <TableHead>Cliente</TableHead>
                    <TableHead>Faculdade</TableHead>
                    <TableHead>Semestre</TableHead>
                    <TableHead>Valor</TableHead>
                    <TableHead>Data Início</TableHead>
                    <TableHead>Data Fim</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {contratosFiltrados.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8 text-gray-500">
                        Nenhum contrato encontrado
                      </TableCell>
                    </TableRow>
                  ) : (
                    contratosFiltrados.map((contrato) => (
                      <TableRow 
                        key={contrato.id}
                        className="cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => abrirDetalhes(contrato)}
                        data-testid={`contrato-row-${contrato.id}`}
                      >
                        <TableCell>
                          {getStatusBadge(contrato.status)}
                        </TableCell>
                        <TableCell>
                          <span className="font-medium">#{contrato.numero_contrato}</span>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <User size={14} className="text-gray-400" />
                            <span className="font-medium">{contrato.cliente}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Building2 size={14} className="text-gray-400" />
                            <span className="text-sm">{contrato.faculdade}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{contrato.semestre}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <DollarSign size={14} className="text-green-600" />
                            <span className="font-semibold text-green-600">
                              {formatarValor(contrato.valor)}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Calendar size={14} className="text-gray-400" />
                            <span className="text-sm">
                              {new Date(contrato.data_inicio).toLocaleDateString('pt-BR')}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Calendar size={14} className="text-gray-400" />
                            <span className="text-sm">
                              {new Date(contrato.data_fim).toLocaleDateString('pt-BR')}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                              e.stopPropagation();
                              abrirDetalhes(contrato);
                            }}
                            data-testid={`ver-detalhes-${contrato.id}`}
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

        {/* Modal de Detalhes do Contrato */}
        <Dialog open={showDetalhesModal} onOpenChange={setShowDetalhesModal}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Detalhes do Contrato</DialogTitle>
              <DialogDescription>
                Visualize e gerencie os detalhes deste contrato
              </DialogDescription>
            </DialogHeader>

            {contratoSelecionado && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">#{contratoSelecionado.numero_contrato}</h3>
                  {getStatusBadge(contratoSelecionado.status)}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm text-gray-500">Cliente</Label>
                    <p className="font-medium mt-1">{contratoSelecionado.cliente}</p>
                  </div>

                  <div>
                    <Label className="text-sm text-gray-500">Faculdade</Label>
                    <p className="font-medium mt-1">{contratoSelecionado.faculdade}</p>
                  </div>

                  <div>
                    <Label className="text-sm text-gray-500">Semestre</Label>
                    <Badge variant="outline" className="mt-1">{contratoSelecionado.semestre}</Badge>
                  </div>

                  <div>
                    <Label className="text-sm text-gray-500">Valor</Label>
                    <p className="font-semibold text-green-600 mt-1">
                      {formatarValor(contratoSelecionado.valor)}
                    </p>
                  </div>

                  <div>
                    <Label className="text-sm text-gray-500">Data de Início</Label>
                    <p className="font-medium mt-1">
                      {new Date(contratoSelecionado.data_inicio).toLocaleDateString('pt-BR')}
                    </p>
                  </div>

                  <div>
                    <Label className="text-sm text-gray-500">Data de Término</Label>
                    <p className="font-medium mt-1">
                      {new Date(contratoSelecionado.data_fim).toLocaleDateString('pt-BR')}
                    </p>
                  </div>
                </div>

                <div className="flex gap-2 pt-4 border-t">
                  {contratoSelecionado.status === 'Ativo' && (
                    <Button
                      onClick={() => aprovarContrato(contratoSelecionado.id)}
                      className="bg-blue-600 hover:bg-blue-700"
                      data-testid="aprovar-contrato-btn"
                    >
                      <CheckCircle2 size={16} className="mr-2" />
                      Aprovar Contrato
                    </Button>
                  )}

                  {contratoSelecionado.status === 'Em Andamento' && (
                    <Button
                      onClick={() => finalizarContrato(contratoSelecionado.id)}
                      className="bg-green-600 hover:bg-green-700"
                      data-testid="finalizar-contrato-btn"
                    >
                      <CheckCircle2 size={16} className="mr-2" />
                      Finalizar Contrato
                    </Button>
                  )}

                  {contratoSelecionado.status === 'Finalizado' && (
                    <div className="w-full text-center py-2 bg-green-50 rounded-lg">
                      <p className="text-green-700 font-medium">✅ Contrato Finalizado</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowDetalhesModal(false)}>
                Fechar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Modal de Novo Contrato */}
        <Dialog open={showNovoModal} onOpenChange={setShowNovoModal}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Novo Contrato</DialogTitle>
              <DialogDescription>
                Preencha os dados para criar um novo contrato
              </DialogDescription>
            </DialogHeader>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="cliente">Cliente *</Label>
                <Input
                  id="cliente"
                  value={novoContrato.cliente}
                  onChange={(e) => setNovoContrato({...novoContrato, cliente: e.target.value})}
                  placeholder="Nome do cliente"
                />
              </div>

              <div>
                <Label htmlFor="faculdade">Faculdade *</Label>
                <Input
                  id="faculdade"
                  value={novoContrato.faculdade}
                  onChange={(e) => setNovoContrato({...novoContrato, faculdade: e.target.value})}
                  placeholder="Nome da faculdade"
                />
              </div>

              <div>
                <Label htmlFor="semestre">Semestre *</Label>
                <Input
                  id="semestre"
                  value={novoContrato.semestre}
                  onChange={(e) => setNovoContrato({...novoContrato, semestre: e.target.value})}
                  placeholder="Ex: 2025/1"
                />
              </div>

              <div>
                <Label htmlFor="valor">Valor *</Label>
                <Input
                  id="valor"
                  type="number"
                  value={novoContrato.valor}
                  onChange={(e) => setNovoContrato({...novoContrato, valor: e.target.value})}
                  placeholder="0.00"
                />
              </div>

              <div>
                <Label htmlFor="data_inicio">Data de Início *</Label>
                <Input
                  id="data_inicio"
                  type="date"
                  value={novoContrato.data_inicio}
                  onChange={(e) => setNovoContrato({...novoContrato, data_inicio: e.target.value})}
                />
              </div>

              <div>
                <Label htmlFor="data_fim">Data de Término *</Label>
                <Input
                  id="data_fim"
                  type="date"
                  value={novoContrato.data_fim}
                  onChange={(e) => setNovoContrato({...novoContrato, data_fim: e.target.value})}
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNovoModal(false)}>
                Cancelar
              </Button>
              <Button onClick={criarContrato} data-testid="criar-contrato-btn">
                <Plus size={16} className="mr-2" />
                Criar Contrato
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
};

export default ContratosLista;
