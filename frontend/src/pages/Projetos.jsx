import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { ArrowRight, AlertTriangle, Clock, CheckCircle } from 'lucide-react';
import { toast } from '../hooks/use-toast';
import axios from 'axios';
import './Projetos.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Projetos = () => {
  const [esteira, setEsteira] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    carregarEsteira();
    const interval = setInterval(carregarEsteira, 30000); // Atualizar a cada 30s
    return () => clearInterval(interval);
  }, []);

  const carregarEsteira = async () => {
    try {
      const response = await axios.get(`${API}/projetos/esteira/visualizacao`);
      setEsteira(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Erro ao carregar esteira:', error);
      toast({ title: 'Erro ao carregar esteira', variant: 'destructive' });
      setLoading(false);
    }
  };

  const avancarMacroEtapa = async (projetoId, cliente) => {
    if (!window.confirm(`Deseja avançar o projeto ${cliente} para a próxima etapa?`)) return;
    
    try {
      const response = await axios.post(`${API}/projetos/${projetoId}/avancar-macro-etapa`);
      
      if (response.data.status === 'success') {
        const dados = response.data.dados_afetados;
        toast({ 
          title: 'Projeto avançado!',
          description: `De ${dados.macro_etapa_anterior} → ${dados.macro_etapa_nova}. ${dados.tarefas_criadas} novas tarefas criadas.`
        });
        carregarEsteira();
      } else if (response.data.status === 'blocked') {
        toast({ 
          title: 'Não foi possível avançar',
          description: response.data.motivo,
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Erro ao avançar macro etapa:', error);
      toast({ title: 'Erro ao avançar projeto', variant: 'destructive' });
    }
  };

  const getRiscoBadge = (risco) => {
    const config = {
      'Baixo': { className: 'bg-green-100 text-green-800', icon: null },
      'Médio': { className: 'bg-yellow-100 text-yellow-800', icon: <Clock size={14} /> },
      'Alto': { className: 'bg-red-100 text-red-800', icon: <AlertTriangle size={14} /> }
    };
    const cfg = config[risco] || config['Baixo'];
    return (
      <Badge className={cfg.className}>
        {cfg.icon && <span className="mr-1">{cfg.icon}</span>}
        {risco}
      </Badge>
    );
  };

  const calcularDiasRestantes = (dataEntrega) => {
    const agora = new Date();
    const entrega = new Date(dataEntrega);
    const diff = Math.ceil((entrega - agora) / (1000 * 60 * 60 * 24));
    return diff;
  };

  if (loading) {
    return (
      <Layout>
        <div className="loading">Carregando esteira...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="projetos-page">
        <div className="page-header">
          <div>
            <h1 className="page-title">Esteira de Projetos</h1>
            <p className="page-subtitle">Visualização do fluxo de produção - Arraste projetos entre etapas</p>
          </div>
        </div>

        <div className="esteira-container">
          {esteira && Object.entries(esteira).map(([key, coluna]) => (
            <div key={key} className="esteira-coluna">
              <div className="coluna-header" style={{ borderTopColor: coluna.cor }}>
                <h3 className="coluna-titulo">{coluna.titulo}</h3>
                <Badge variant="outline" className="coluna-contador">
                  {coluna.projetos.length}
                </Badge>
              </div>

              <div className="coluna-projetos">
                {coluna.projetos.length === 0 ? (
                  <div className="coluna-vazia">
                    <p>Nenhum projeto nesta etapa</p>
                  </div>
                ) : (
                  coluna.projetos.map((projeto) => {
                    const diasRestantes = calcularDiasRestantes(projeto.data_entrega);
                    const isCritico = diasRestantes <= 7;
                    const isAtencao = diasRestantes <= 15 && diasRestantes > 7;
                    const isCompleto = projeto.progresso === 100;
                    const isUltimaColuna = key === 'POS_PRODUCAO';
                    
                    return (
                      <Card 
                        key={projeto.id} 
                        className={`projeto-card ${isCritico ? 'border-red-500' : isAtencao ? 'border-yellow-500' : ''}`}
                      >
                        <CardHeader className="pb-3">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="text-xs text-gray-500 mb-1">
                                #{projeto.numero_contrato}
                              </div>
                              <CardTitle className="text-base">{projeto.cliente}</CardTitle>
                              <div className="text-xs text-gray-600 mt-1">
                                {projeto.faculdade}
                              </div>
                            </div>
                            {getRiscoBadge(projeto.risco)}
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            <div>
                              <div className="flex justify-between text-xs mb-1">
                                <span className="text-gray-600">Progresso</span>
                                <span className="font-medium">{projeto.progresso}%</span>
                              </div>
                              <Progress value={projeto.progresso} className="h-2" />
                            </div>

                            <div className="text-xs">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-gray-600">Etapa:</span>
                                <span className="text-gray-900 font-medium text-right">
                                  {projeto.etapa_atual.replace(/^\d+\s*-\s*/, '')}
                                </span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="text-gray-600">Entrega:</span>
                                <span className={`font-medium ${isCritico ? 'text-red-600' : isAtencao ? 'text-yellow-600' : 'text-gray-900'}`}>
                                  {diasRestantes > 0 ? `${diasRestantes} dias` : 'ATRASADO'}
                                </span>
                              </div>
                            </div>

                            {isCritico && (
                              <div className="bg-red-50 border border-red-200 rounded p-2 text-xs text-red-700 flex items-center gap-1">
                                <AlertTriangle size={12} />
                                <span className="font-medium">CRÍTICO - Entrega próxima!</span>
                              </div>
                            )}

                            {/* Botão para avançar macro etapa */}
                            {!isUltimaColuna && (
                              <Button
                                size="sm"
                                className="w-full mt-2"
                                onClick={() => avancarMacroEtapa(projeto.id, projeto.cliente)}
                                variant={isCompleto ? "default" : "outline"}
                              >
                                {isCompleto ? (
                                  <>
                                    <CheckCircle size={14} className="mr-1" />
                                    Avançar para {key === 'PRE_PRODUCAO' ? 'Produção' : 'Pós-Produção'}
                                  </>
                                ) : (
                                  <>
                                    <ArrowRight size={14} className="mr-1" />
                                    Avançar Etapa
                                  </>
                                )}
                              </Button>
                            )}

                            {isUltimaColuna && (
                              <div className="bg-green-50 border border-green-200 rounded p-2 text-xs text-green-700 flex items-center gap-1 justify-center">
                                <CheckCircle size={12} />
                                <span className="font-medium">Projeto Concluído</span>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
};

export default Projetos;
