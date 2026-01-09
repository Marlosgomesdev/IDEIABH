import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import { AlertTriangle, TrendingUp, Clock, CheckCircle, XCircle } from 'lucide-react';
import axios from 'axios';
import './Dashboard.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    carregarDashboard();
  }, []);

  const carregarDashboard = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboard(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="dashboard-loading">Carregando dashboard...</div>
      </Layout>
    );
  }

  const kpis = dashboard?.kpis || {};
  const tarefasAtrasadas = dashboard?.tarefas_atrasadas || [];
  const projetosPorStatus = dashboard?.projetos_por_status || {};
  const gargalos = dashboard?.gargalos_responsaveis || [];

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
              <div className="kpi-value">{kpis.percentual_no_prazo}%</div>
              <Progress value={kpis.percentual_no_prazo} className="kpi-progress" />
            </CardContent>
          </Card>

          <Card className="kpi-card">
            <CardHeader className="kpi-header">
              <CheckCircle className="kpi-icon" style={{ color: '#3b82f6' }} />
              <CardTitle className="kpi-title">Total de Projetos</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="kpi-value">{kpis.total_projetos}</div>
              <p className="kpi-description">Em gestão</p>
            </CardContent>
          </Card>

          <Card className="kpi-card alert-high">
            <CardHeader className="kpi-header">
              <AlertTriangle className="kpi-icon" style={{ color: '#ef4444' }} />
              <CardTitle className="kpi-title">Risco Alto</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="kpi-value">{kpis.projetos_risco_alto}</div>
              <p className="kpi-description">Projetos críticos</p>
            </CardContent>
          </Card>

          <Card className="kpi-card alert-medium">
            <CardHeader className="kpi-header">
              <Clock className="kpi-icon" style={{ color: '#f59e0b' }} />
              <CardTitle className="kpi-title">Tarefas Atrasadas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="kpi-value">{kpis.tarefas_atrasadas_total}</div>
              <p className="kpi-description">Requer atenção</p>
            </CardContent>
          </Card>
        </div>

        {/* Projetos por Status */}
        <div className="dashboard-section">
          <Card>
            <CardHeader>
              <CardTitle>Projetos por Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="status-list">
                {Object.entries(projetosPorStatus).map(([status, count]) => (
                  <div key={status} className="status-item">
                    <div className="status-info">
                      <span className="status-name">{status}</span>
                      <Badge variant="outline">{count}</Badge>
                    </div>
                    <Progress 
                      value={(count / kpis.total_projetos) * 100} 
                      className="status-progress" 
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tarefas Atrasadas */}
        {tarefasAtrasadas.length > 0 && (
          <div className="dashboard-section">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle size={20} className="text-red-500" />
                  Tarefas Atrasadas (Urgência)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="tarefas-list">
                  {tarefasAtrasadas.map((tarefa) => (
                    <div key={tarefa.id} className="tarefa-item">
                      <div className="tarefa-info">
                        <XCircle size={18} className="text-red-500" />
                        <div>
                          <p className="tarefa-titulo">{tarefa.titulo}</p>
                          <p className="tarefa-responsavel">Responsável: {tarefa.responsavel}</p>
                        </div>
                      </div>
                      <Badge variant="destructive">{tarefa.dias_atraso} dias atrasada</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Gargalos */}
        {gargalos.length > 0 && (
          <div className="dashboard-section">
            <Card>
              <CardHeader>
                <CardTitle>Gargalos por Responsável</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="gargalos-list">
                  {gargalos.map(([responsavel, count]) => (
                    <div key={responsavel} className="gargalo-item">
                      <span className="gargalo-nome">{responsavel}</span>
                      <div className="gargalo-info">
                        <span className="gargalo-count">{count} tarefas pendentes</span>
                        <Progress value={Math.min((count / 10) * 100, 100)} className="gargalo-progress" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Dashboard;