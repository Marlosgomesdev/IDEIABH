import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { AlertTriangle, TrendingUp, Clock, CheckCircle, User, Calendar } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import axios from 'axios';
import './Dashboard.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COLORS = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6'];

const DashboardNovo = () => {
  const [tarefasAtrasadas, setTarefasAtrasadas] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModalAtrasadas, setShowModalAtrasadas] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    carregarDados();
    // Auto-refresh a cada 60 segundos
    const interval = setInterval(carregarDados, 60000);
    return () => clearInterval(interval);
  }, []);

  const getToken = () => localStorage.getItem('token');

  const carregarDados = async () => {
    try {
      const token = getToken();
      
      // Carregar dashboard básico
      const dashResponse = await axios.get(`${API}/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboard(dashResponse.data);

      // Carregar tarefas atrasadas
      const atrasadasResponse = await axios.get(`${API}/dashboard/tarefas-atrasadas`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTarefasAtrasadas(atrasadasResponse.data.tarefas || []);
      
      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
      setLoading(false);
    }
  };

  const abrirModalAtrasadas = () => {
    setShowModalAtrasadas(true);
  };

  const verTarefa = (tarefaId) => {
    setShowModalAtrasadas(false);
    navigate('/tarefas');
  };

  if (loading) {
    return (
      <Layout>
        <div className="dashboard-loading">Carregando dashboard...</div>
      </Layout>
    );
  }

  const kpis = dashboard?.kpis || {};
  const projetosPorStatus = dashboard?.projetos_por_status || {};
  const gargalos = dashboard?.gargalos_responsaveis || [];

  // Preparar dados para gráfico de tarefas atrasadas por responsável
  const dadosGraficoAtrasadas = Object.entries(
    tarefasAtrasadas.reduce((acc, tarefa) => {
      const resp = tarefa.responsavel || 'Não atribuído';
      acc[resp] = (acc[resp] || 0) + 1;
      return acc;
    }, {})
  ).map(([nome, quantidade]) => ({ nome, quantidade }));

  // Dados para gráfico de pizza de status
  const dadosGraficoPizza = Object.entries(projetosPorStatus).map(([status, quantidade]) => ({
    name: status,
    value: quantidade
  }));

  return (
    <Layout>
      <div className="dashboard">
        <div className="dashboard-header">
          <div>
            <h1 className="dashboard-title">Dashboard Gerencial</h1>
            <p className="dashboard-subtitle">Visão geral dos projetos e operações</p>
          </div>
          <Link to="/contratos" className="btn-primary">
            Novo Contrato
          </Link>
        </div>

        {/* KPIs */}
        <div className="kpi-grid">
          <Card className="kpi-card">
            <CardHeader className="kpi-header">
              <TrendingUp className="kpi-icon" style={{ color: '#10b981' }} />
              <CardTitle className="kpi-title">Projetos no Prazo</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="kpi-value">{kpis.percentual_no_prazo || 0}%</div>
              <p className="kpi-description">Taxa de sucesso</p>
            </CardContent>
          </Card>

          <Card className="kpi-card">
            <CardHeader className="kpi-header">
              <CheckCircle className="kpi-icon" style={{ color: '#3b82f6' }} />
              <CardTitle className="kpi-title">Total de Projetos</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="kpi-value">{kpis.total_projetos || 0}</div>
              <p className="kpi-description">Em gestão</p>
            </CardContent>
          </Card>

          <Card className="kpi-card alert-high">
            <CardHeader className="kpi-header">
              <AlertTriangle className="kpi-icon" style={{ color: '#ef4444' }} />
              <CardTitle className="kpi-title">Risco Alto</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="kpi-value">{kpis.projetos_risco_alto || 0}</div>
              <p className="kpi-description">Projetos críticos</p>
            </CardContent>
          </Card>

          <Card 
            className="kpi-card alert-medium cursor-pointer hover:shadow-lg transition-shadow" 
            onClick={abrirModalAtrasadas}
            data-testid="card-tarefas-atrasadas"
          >
            <CardHeader className="kpi-header">
              <Clock className="kpi-icon" style={{ color: '#f59e0b' }} />
              <CardTitle className="kpi-title">Tarefas Atrasadas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="kpi-value">{tarefasAtrasadas.length}</div>
              <p className="kpi-description">Clique para ver detalhes</p>
            </CardContent>
          </Card>
        </div>

        {/* Gráficos */}
        <div className="graficos-grid">
          {/* Gráfico de Barras - Tarefas Atrasadas por Responsável */}
          {dadosGraficoAtrasadas.length > 0 && (
            <Card className="grafico-card">
              <CardHeader>
                <CardTitle>Tarefas Atrasadas por Responsável</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={dadosGraficoAtrasadas}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="nome" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="quantidade" fill="#ef4444" name="Tarefas Atrasadas" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Gráfico de Pizza - Projetos por Status */}
          {dadosGraficoPizza.length > 0 && (
            <Card className="grafico-card">
              <CardHeader>
                <CardTitle>Projetos por Status</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={dadosGraficoPizza}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {dadosGraficoPizza.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Gargalos */}
        {gargalos.length > 0 && (
          <Card className="gargalos-card">
            <CardHeader>
              <CardTitle>Gargalos por Responsável</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="gargalos-list">
                {gargalos.map((g, index) => (
                  <div key={index} className="gargalo-item">
                    <div className="gargalo-info">
                      <User size={16} className="text-gray-400" />
                      <span className="font-medium">{g.responsavel}</span>
                    </div>
                    <Badge variant="destructive">{g.tarefas_pendentes} tarefas pendentes</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Modal de Tarefas Atrasadas */}
        <Dialog open={showModalAtrasadas} onOpenChange={setShowModalAtrasadas}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <AlertTriangle className="text-red-500" />
                Tarefas Atrasadas ({tarefasAtrasadas.length})
              </DialogTitle>
              <DialogDescription>
                Lista completa de tarefas com prazos vencidos
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3">
              {tarefasAtrasadas.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle size={48} className="mx-auto mb-2 opacity-50" />
                  <p>Nenhuma tarefa atrasada! 🎉</p>
                </div>
              ) : (
                tarefasAtrasadas.map((tarefa) => (
                  <Card key={tarefa.id} className="border-l-4 border-l-red-500">
                    <CardContent className="pt-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-semibold text-lg mb-2">{tarefa.titulo}</h4>
                          <div className="grid grid-cols-2 gap-3 text-sm">
                            <div className="flex items-center gap-2">
                              <User size={14} className="text-gray-400" />
                              <span>{tarefa.responsavel}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Calendar size={14} className="text-gray-400" />
                              <span>Prazo: {new Date(tarefa.prazo).toLocaleDateString('pt-BR')}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Clock size={14} className="text-gray-400" />
                              <span className="text-red-600 font-semibold">
                                {tarefa.dias_atraso} dias de atraso
                              </span>
                            </div>
                            <div>
                              <Badge variant="outline">{tarefa.setor}</Badge>
                            </div>
                          </div>
                          {tarefa.observacao && (
                            <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
                              <p className="text-sm text-yellow-800">
                                <strong>Justificativa:</strong> {tarefa.observacao}
                              </p>
                            </div>
                          )}
                        </div>
                        <Button
                          size="sm"
                          onClick={() => verTarefa(tarefa.id)}
                          className="ml-4"
                        >
                          Ver Detalhes
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
};

export default DashboardNovo;