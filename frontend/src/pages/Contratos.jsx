import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { Plus, Edit, Trash2, Check, X, Flag } from 'lucide-react';
import { toast } from '../hooks/use-toast';
import axios from 'axios';
import './Contratos.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Contratos = () => {
  const [contratos, setContratos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editando, setEditando] = useState(null);
  
  const [formData, setFormData] = useState({
    numero_contrato: '',
    cliente: '',
    faculdade: '',
    semestre: '',
    valor: '',
    data_inicio: '',
    data_fim: ''
  });

  useEffect(() => {
    carregarContratos();
  }, []);

  const carregarContratos = async () => {
    try {
      const response = await axios.get(`${API}/contratos`);
      setContratos(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar contratos:', error);
      toast({ title: 'Erro ao carregar contratos', variant: 'destructive' });
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const dados = {
        ...formData,
        numero_contrato: parseInt(formData.numero_contrato),
        valor: parseFloat(formData.valor),
        data_inicio: new Date(formData.data_inicio).toISOString(),
        data_fim: new Date(formData.data_fim).toISOString()
      };

      if (editando) {
        const response = await axios.put(`${API}/contratos/${editando}`, dados);
        if (response.data.status === 'success') {
          toast({ title: 'Contrato atualizado com sucesso!' });
        }
      } else {
        const response = await axios.post(`${API}/contratos`, dados);
        if (response.data.status === 'success') {
          toast({ title: `Contrato criado! ${response.data.dados_afetados.tarefas_criadas} tarefas geradas.` });
        }
      }
      
      setModalOpen(false);
      resetForm();
      carregarContratos();
    } catch (error) {
      console.error('Erro ao salvar contrato:', error);
      toast({ title: 'Erro ao salvar contrato', variant: 'destructive' });
    }
  };

  const aprovarContrato = async (contratoId) => {
    if (!window.confirm('Deseja aprovar este contrato? Isso iniciará o projeto e gerará novas tarefas.')) return;
    
    try {
      const response = await axios.put(`${API}/contratos/${contratoId}/aprovar`);
      
      if (response.data.status === 'success') {
        toast({ title: `Contrato aprovado! ${response.data.dados_afetados.tarefas_criadas} tarefas criadas.` });
        carregarContratos();
      } else {
        toast({ title: response.data.motivo, variant: 'destructive' });
      }
    } catch (error) {
      console.error('Erro ao aprovar contrato:', error);
      toast({ title: 'Erro ao aprovar contrato', variant: 'destructive' });
    }
  };

  const finalizarContrato = async (contratoId) => {
    if (!window.confirm('Deseja finalizar este contrato? Certifique-se que todas as tarefas estão concluídas.')) return;
    
    try {
      const response = await axios.put(`${API}/contratos/${contratoId}/finalizar`);
      
      if (response.data.status === 'blocked') {
        toast({ title: response.data.motivo, variant: 'destructive' });
      } else {
        toast({ title: 'Contrato finalizado com sucesso!' });
        carregarContratos();
      }
    } catch (error) {
      console.error('Erro ao finalizar contrato:', error);
      toast({ title: 'Erro ao finalizar contrato', variant: 'destructive' });
    }
  };

  const excluirContrato = async (contratoId) => {
    if (!window.confirm('Tem certeza que deseja excluir este contrato?')) return;
    
    try {
      const response = await axios.delete(`${API}/contratos/${contratoId}`);
      
      if (response.data.status === 'blocked') {
        toast({ title: response.data.motivo, variant: 'destructive' });
      } else {
        toast({ title: 'Contrato excluído com sucesso!' });
        carregarContratos();
      }
    } catch (error) {
      console.error('Erro ao excluir contrato:', error);
      toast({ title: 'Erro ao excluir contrato', variant: 'destructive' });
    }
  };

  const resetForm = () => {
    setFormData({
      numero_contrato: '',
      cliente: '',
      faculdade: '',
      semestre: '',
      valor: '',
      data_inicio: '',
      data_fim: ''
    });
    setEditando(null);
  };

  const abrirModal = (contrato = null) => {
    if (contrato) {
      setEditando(contrato.id);
      setFormData({
        numero_contrato: contrato.numero_contrato,
        cliente: contrato.cliente,
        faculdade: contrato.faculdade,
        semestre: contrato.semestre,
        valor: contrato.valor,
        data_inicio: contrato.data_inicio.split('T')[0],
        data_fim: contrato.data_fim.split('T')[0]
      });
    } else {
      resetForm();
    }
    setModalOpen(true);
  };

  const getStatusBadge = (status) => {
    const config = {
      'Ativo': { variant: 'default', className: 'bg-blue-100 text-blue-800' },
      'Em Andamento': { variant: 'default', className: 'bg-yellow-100 text-yellow-800' },
      'Finalizado': { variant: 'outline', className: 'bg-green-100 text-green-800' },
      'Encerrado': { variant: 'outline', className: 'bg-gray-100 text-gray-800' }
    };
    const cfg = config[status] || config['Ativo'];
    return <Badge variant={cfg.variant} className={cfg.className}>{status}</Badge>;
  };

  return (
    <Layout>
      <div className="contratos-page">
        <div className="page-header">
          <div>
            <h1 className="page-title">Contratos</h1>
            <p className="page-subtitle">Gerenciar contratos e iniciar projetos</p>
          </div>
          <Button onClick={() => abrirModal()} className="btn-primary">
            <Plus size={18} className="mr-2" />
            Novo Contrato
          </Button>
        </div>

        {loading ? (
          <div className="loading">Carregando...</div>
        ) : (
          <div className="contratos-grid">
            {contratos.map((contrato) => (
              <Card key={contrato.id} className="contrato-card">
                <CardHeader>
                  <div className="card-header-content">
                    <div>
                      <div className="text-xs text-gray-500 mb-1">#{contrato.numero_contrato}</div>
                      <CardTitle className="text-lg">{contrato.cliente}</CardTitle>
                      <div className="text-sm text-gray-600 mt-1">{contrato.faculdade}</div>
                    </div>
                    {getStatusBadge(contrato.status)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="contrato-info">
                    <div className="info-item">
                      <span className="info-label">Semestre:</span>
                      <span className="info-value">{contrato.semestre}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Valor:</span>
                      <span className="info-value font-bold text-green-600">R$ {contrato.valor.toLocaleString('pt-BR')}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Início:</span>
                      <span className="info-value">{new Date(contrato.data_inicio).toLocaleDateString('pt-BR')}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Entrega:</span>
                      <span className="info-value">{new Date(contrato.data_fim).toLocaleDateString('pt-BR')}</span>
                    </div>
                  </div>

                  <div className="card-actions mt-4">
                    {contrato.status === 'Ativo' && (
                      <Button 
                        size="sm" 
                        className="bg-green-600 hover:bg-green-700"
                        onClick={() => aprovarContrato(contrato.id)}
                      >
                        <Check size={16} className="mr-1" />
                        Aprovar
                      </Button>
                    )}
                    
                    {contrato.status === 'Em Andamento' && (
                      <Button 
                        size="sm" 
                        className="bg-blue-600 hover:bg-blue-700"
                        onClick={() => finalizarContrato(contrato.id)}
                      >
                        <Flag size={16} className="mr-1" />
                        Finalizar
                      </Button>
                    )}
                    
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => abrirModal(contrato)}
                    >
                      <Edit size={16} />
                    </Button>
                    <Button 
                      size="sm" 
                      variant="destructive" 
                      onClick={() => excluirContrato(contrato.id)}
                    >
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <Dialog open={modalOpen} onOpenChange={setModalOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{editando ? 'Editar Contrato' : 'Novo Contrato'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="form-modal">
              <div className="grid grid-cols-2 gap-4">
                <div className="form-group">
                  <Label htmlFor="numero_contrato">Número do Contrato</Label>
                  <Input
                    id="numero_contrato"
                    type="number"
                    value={formData.numero_contrato}
                    onChange={(e) => setFormData({...formData, numero_contrato: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <Label htmlFor="semestre">Semestre</Label>
                  <Input
                    id="semestre"
                    placeholder="Ex: 2025/1"
                    value={formData.semestre}
                    onChange={(e) => setFormData({...formData, semestre: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group col-span-2">
                  <Label htmlFor="cliente">Cliente</Label>
                  <Input
                    id="cliente"
                    placeholder="Ex: MEDICINA UFU"
                    value={formData.cliente}
                    onChange={(e) => setFormData({...formData, cliente: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group col-span-2">
                  <Label htmlFor="faculdade">Faculdade</Label>
                  <Input
                    id="faculdade"
                    placeholder="Ex: Universidade Federal de Uberlândia"
                    value={formData.faculdade}
                    onChange={(e) => setFormData({...formData, faculdade: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <Label htmlFor="valor">Valor (R$)</Label>
                  <Input
                    id="valor"
                    type="number"
                    step="0.01"
                    value={formData.valor}
                    onChange={(e) => setFormData({...formData, valor: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <Label htmlFor="data_inicio">Data Início</Label>
                  <Input
                    id="data_inicio"
                    type="date"
                    value={formData.data_inicio}
                    onChange={(e) => setFormData({...formData, data_inicio: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group col-span-2">
                  <Label htmlFor="data_fim">Data de Entrega</Label>
                  <Input
                    id="data_fim"
                    type="date"
                    value={formData.data_fim}
                    onChange={(e) => setFormData({...formData, data_fim: e.target.value})}
                    required
                  />
                </div>
              </div>
              <div className="form-actions">
                <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
                  Cancelar
                </Button>
                <Button type="submit">
                  {editando ? 'Atualizar' : 'Criar Contrato'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
};

export default Contratos;
