#!/usr/bin/env python3
"""
IDEIABH Sistema de Gestão Operacional - Bateria COMPLETA de Testes
Executa todos os testes conforme especificado na review request em português
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
from dotenv import load_dotenv
import urllib.parse

# Carregar variáveis de ambiente
load_dotenv('/app/frontend/.env')

# Configuração da API
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://govflux-mirror.preview.emergentagent.com')
API_URL = f"{BASE_URL}/api"

class IDEIABHTestCompleto:
    def __init__(self):
        self.session = requests.Session()
        self.contratos_criados = []
        self.projetos_criados = []
        self.tarefas_criadas = []
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': [],
            'critical_errors': []
        }
    
    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None, critical: bool = False):
        """Log do resultado do teste"""
        self.test_results['total_tests'] += 1
        if success:
            self.test_results['passed'] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.test_results['failed'] += 1
            error_msg = f"❌ {test_name}: {message}"
            if data:
                error_msg += f"\nDados: {json.dumps(data, indent=2, default=str)}"
            print(error_msg)
            self.test_results['errors'].append(error_msg)
            if critical:
                self.test_results['critical_errors'].append(error_msg)
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Faz requisição para a API"""
        url = f"{API_URL}{endpoint}"
        try:
            headers = {'Content-Type': 'application/json'}
            
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers)
            
            print(f"🔄 {method} {url} - Status: {response.status_code}")
            
            if response.status_code >= 400:
                print(f"❌ Erro na requisição: {response.text}")
            
            return {
                'status_code': response.status_code,
                'data': response.json() if response.content else {},
                'success': 200 <= response.status_code < 300,
                'raw_response': response.text
            }
        except Exception as e:
            print(f"❌ Erro na requisição {method} {url}: {str(e)}")
            return {
                'status_code': 0,
                'data': {},
                'success': False,
                'error': str(e)
            }
    
    def limpar_banco_dados(self):
        """Limpa o banco de dados completamente"""
        print("\n🧹 LIMPANDO BANCO DE DADOS")
        
        # Listar e excluir todos os contratos
        response_contratos = self.make_request('GET', '/contratos')
        if response_contratos['success']:
            contratos = response_contratos['data']
            print(f"📋 Encontrados {len(contratos)} contratos para excluir")
            
            for contrato in contratos:
                contrato_id = contrato.get('id')
                if contrato_id:
                    response_delete = self.make_request('DELETE', f'/contratos/{contrato_id}')
                    if response_delete['success']:
                        print(f"  ✅ Contrato {contrato_id} excluído")
                    else:
                        print(f"  ❌ Falha ao excluir contrato {contrato_id}")
        
        print("✅ Limpeza do banco concluída")
    
    def teste_1_health_check(self):
        """TESTE 1: HEALTH CHECK - GET /api/"""
        print("\n🔍 TESTE 1: HEALTH CHECK")
        print("Verificando se backend está online...")
        
        response = self.make_request('GET', '/')
        
        if response['success']:
            data = response['data']
            if data.get('sistema') == 'IDEIABH' and data.get('status') == 'operacional':
                self.log_test("Health Check", True, "Backend está online e operacional")
                return True
            else:
                self.log_test("Health Check", False, "Resposta não conforme esperado", data, critical=True)
                return False
        else:
            self.log_test("Health Check", False, f"Backend não respondeu - Status: {response['status_code']}", critical=True)
            return False
    
    def teste_2_limpar_e_criar_contratos(self):
        """TESTE 2: LIMPAR BANCO E CRIAR CONTRATOS"""
        print("\n🔍 TESTE 2: LIMPAR BANCO E CRIAR 3 CONTRATOS")
        
        # Limpar banco
        self.limpar_banco_dados()
        
        hoje = datetime.now()
        
        contratos_dados = [
            {
                "numero_contrato": 1,
                "cliente": "MEDICINA UFU",
                "faculdade": "Universidade Federal de Uberlândia",
                "semestre": "2025/1",
                "valor": 50000,
                "data_inicio": hoje.isoformat(),
                "data_fim": (hoje + timedelta(days=90)).isoformat()
            },
            {
                "numero_contrato": 2,
                "cliente": "DIREITO UNEB",
                "faculdade": "UNEB",
                "semestre": "2025/1",
                "valor": 35000,
                "data_inicio": hoje.isoformat(),
                "data_fim": (hoje + timedelta(days=60)).isoformat()
            },
            {
                "numero_contrato": 3,
                "cliente": "ODONTOLOGIA UNIFESO",
                "faculdade": "UNIFESO",
                "semestre": "2025/2",
                "valor": 42000,
                "data_inicio": hoje.isoformat(),
                "data_fim": (hoje + timedelta(days=75)).isoformat()
            }
        ]
        
        contratos_criados_com_sucesso = 0
        
        for i, contrato_data in enumerate(contratos_dados, 1):
            print(f"\n📝 Criando Contrato {i}: {contrato_data['cliente']}")
            
            response = self.make_request('POST', '/contratos', contrato_data)
            
            if response['success']:
                data = response['data']
                if data.get('status') == 'success':
                    contrato_id = data.get('dados_afetados', {}).get('contrato_id')
                    projeto_id = data.get('dados_afetados', {}).get('projeto_id')
                    tarefas_criadas = data.get('dados_afetados', {}).get('tarefas_criadas', 0)
                    
                    self.contratos_criados.append({
                        'id': contrato_id,
                        'projeto_id': projeto_id,
                        'cliente': contrato_data['cliente'],
                        'numero': contrato_data['numero_contrato'],
                        'valor': contrato_data['valor']
                    })
                    
                    self.log_test(f"Criar Contrato {i}", True, 
                                f"Contrato criado - ID: {contrato_id}, Projeto: {projeto_id}, Tarefas: {tarefas_criadas}")
                    contratos_criados_com_sucesso += 1
                else:
                    self.log_test(f"Criar Contrato {i}", False, 
                                f"Status não é success: {data.get('status')}", data, critical=True)
            else:
                self.log_test(f"Criar Contrato {i}", False, 
                            f"Falha na requisição - Status: {response['status_code']}", response['data'], critical=True)
        
        if contratos_criados_com_sucesso == 3:
            self.log_test("Criação de 3 Contratos", True, "Todos os 3 contratos foram criados com dados completos")
            return True
        else:
            self.log_test("Criação de 3 Contratos", False, 
                        f"Apenas {contratos_criados_com_sucesso}/3 contratos foram criados", critical=True)
            return False
    
    def teste_3_aprovar_contrato(self):
        """TESTE 3: APROVAR CONTRATO"""
        print("\n🔍 TESTE 3: APROVAR CONTRATO")
        
        if not self.contratos_criados:
            self.log_test("Aprovar Contrato", False, "Nenhum contrato disponível para aprovação", critical=True)
            return False
        
        primeiro_contrato = self.contratos_criados[0]
        contrato_id = primeiro_contrato['id']
        cliente = primeiro_contrato['cliente']
        
        print(f"📋 Aprovando contrato: {cliente}")
        
        # Aprovar contrato
        response = self.make_request('PUT', f'/contratos/{contrato_id}/aprovar')
        
        if response['success']:
            data = response['data']
            if data.get('status') == 'success':
                status_novo = data.get('dados_afetados', {}).get('status_novo')
                tarefas_criadas = data.get('dados_afetados', {}).get('tarefas_criadas', 0)
                
                self.log_test("Aprovar Contrato", True, 
                            f"Contrato aprovado - Status: {status_novo}, Tarefas geradas: {tarefas_criadas}")
                
                # Verificar se status mudou para "Em Andamento"
                response_contrato = self.make_request('GET', f'/contratos/{contrato_id}')
                if response_contrato['success']:
                    contrato = response_contrato['data']
                    status_atual = contrato.get('status')
                    
                    if status_atual == 'Em Andamento':
                        self.log_test("Status Em Andamento", True, "Status mudou corretamente para 'Em Andamento'")
                    else:
                        self.log_test("Status Em Andamento", False, f"Status atual: {status_atual}, esperado: 'Em Andamento'")
                
                # Verificar se tarefas foram geradas
                projeto_id = primeiro_contrato['projeto_id']
                response_tarefas = self.make_request('GET', f'/tarefas?projeto_id={projeto_id}')
                if response_tarefas['success']:
                    tarefas = response_tarefas['data']
                    self.log_test("Tarefas Geradas", True, f"Encontradas {len(tarefas)} tarefas após aprovação")
                
                # Testar erro ao aprovar contrato já aprovado
                print("\n🔄 Testando aprovação de contrato já aprovado...")
                response_dupla = self.make_request('PUT', f'/contratos/{contrato_id}/aprovar')
                
                if not response_dupla['success'] or response_dupla['data'].get('status') == 'blocked':
                    self.log_test("Erro Dupla Aprovação", True, "Sistema bloqueou corretamente aprovação duplicada")
                else:
                    self.log_test("Erro Dupla Aprovação", False, "Sistema não bloqueou aprovação duplicada")
                
                return True
            else:
                self.log_test("Aprovar Contrato", False, f"Status não é success: {data.get('status')}", data, critical=True)
                return False
        else:
            self.log_test("Aprovar Contrato", False, 
                        f"Falha na requisição - Status: {response['status_code']}", response['data'], critical=True)
            return False
    
    def teste_4_visualizacao_esteira(self):
        """TESTE 4: VISUALIZAÇÃO DA ESTEIRA"""
        print("\n🔍 TESTE 4: VISUALIZAÇÃO DA ESTEIRA")
        
        response = self.make_request('GET', '/projetos/esteira/visualizacao')
        
        if response['success']:
            esteira = response['data']
            
            # Verificar se retorna as 3 colunas
            colunas_esperadas = ['PRE_PRODUCAO', 'PRODUCAO', 'POS_PRODUCAO']
            colunas_presentes = all(coluna in esteira for coluna in colunas_esperadas)
            
            if colunas_presentes:
                self.log_test("Colunas da Esteira", True, "Todas as 3 colunas estão presentes")
                
                # Verificar se projetos estão nas colunas corretas
                total_projetos = 0
                for coluna in colunas_esperadas:
                    projetos_coluna = esteira[coluna].get('projetos', [])
                    total_projetos += len(projetos_coluna)
                    print(f"  📊 {esteira[coluna].get('titulo')}: {len(projetos_coluna)} projetos")
                
                self.log_test("Projetos na Esteira", True, f"Total de {total_projetos} projetos organizados na esteira")
                
                # Verificar estrutura das colunas
                estrutura_correta = True
                for coluna in colunas_esperadas:
                    coluna_data = esteira[coluna]
                    if not all(key in coluna_data for key in ['titulo', 'cor', 'projetos']):
                        estrutura_correta = False
                        break
                
                if estrutura_correta:
                    self.log_test("Estrutura da Esteira", True, "Estrutura das colunas está correta")
                    return True
                else:
                    self.log_test("Estrutura da Esteira", False, "Estrutura das colunas está incorreta", esteira)
                    return False
            else:
                colunas_faltando = [c for c in colunas_esperadas if c not in esteira]
                self.log_test("Colunas da Esteira", False, f"Colunas faltando: {colunas_faltando}", esteira, critical=True)
                return False
        else:
            self.log_test("Visualização da Esteira", False, 
                        f"Erro ao acessar esteira - Status: {response['status_code']}", response['data'], critical=True)
            return False
    
    def teste_5_kanban_tarefas(self):
        """TESTE 5: KANBAN DE TAREFAS"""
        print("\n🔍 TESTE 5: KANBAN DE TAREFAS")
        
        if not self.contratos_criados:
            self.log_test("Kanban de Tarefas", False, "Nenhum projeto disponível para testar kanban", critical=True)
            return False
        
        primeiro_projeto = self.contratos_criados[0]
        projeto_id = primeiro_projeto['projeto_id']
        cliente = primeiro_projeto['cliente']
        
        print(f"📋 Testando kanban do projeto: {cliente}")
        
        response = self.make_request('GET', f'/tarefas/kanban/{projeto_id}')
        
        if response['success']:
            kanban = response['data']
            
            # Verificar se retorna todas as colunas do kanban
            colunas_esperadas = [
                'LANCAMENTO', 'ATIVACAO', 'REVISAO', 'CRIACAO_1_2', 
                'CRIACAO_3_4', 'APROVACAO', 'PLANEJAMENTO', 'PRE_PRODUCAO', 
                'PRODUCAO', 'CONCLUIDO'
            ]
            
            colunas_presentes = all(coluna in kanban for coluna in colunas_esperadas)
            
            if colunas_presentes:
                self.log_test("Colunas do Kanban", True, f"Todas as {len(colunas_esperadas)} colunas estão presentes")
                
                # Verificar se as tarefas estão organizadas corretamente
                total_tarefas = 0
                for coluna in colunas_esperadas:
                    tarefas_coluna = kanban[coluna].get('tarefas', [])
                    total_tarefas += len(tarefas_coluna)
                    if len(tarefas_coluna) > 0:
                        print(f"  📋 {kanban[coluna].get('titulo')}: {len(tarefas_coluna)} tarefas")
                
                self.log_test("Tarefas Organizadas", True, f"Total de {total_tarefas} tarefas organizadas no kanban")
                
                # Verificar estrutura das colunas
                estrutura_correta = True
                for coluna in colunas_esperadas:
                    coluna_data = kanban[coluna]
                    if not all(key in coluna_data for key in ['titulo', 'cor', 'tarefas']):
                        estrutura_correta = False
                        break
                
                if estrutura_correta:
                    self.log_test("Estrutura do Kanban", True, "Estrutura das colunas do kanban está correta")
                    return True
                else:
                    self.log_test("Estrutura do Kanban", False, "Estrutura das colunas do kanban está incorreta", kanban)
                    return False
            else:
                colunas_faltando = [c for c in colunas_esperadas if c not in kanban]
                self.log_test("Colunas do Kanban", False, f"Colunas faltando: {colunas_faltando}", kanban, critical=True)
                return False
        else:
            self.log_test("Kanban de Tarefas", False, 
                        f"Erro ao acessar kanban - Status: {response['status_code']}", response['data'], critical=True)
            return False
    
    def teste_6_mover_tarefa(self):
        """TESTE 6: MOVER TAREFA (Drag and Drop)"""
        print("\n🔍 TESTE 6: MOVER TAREFA (Drag and Drop)")
        
        if not self.contratos_criados:
            self.log_test("Mover Tarefa", False, "Nenhum projeto disponível para testar movimento", critical=True)
            return False
        
        primeiro_projeto = self.contratos_criados[0]
        projeto_id = primeiro_projeto['projeto_id']
        
        # Buscar primeira tarefa do projeto
        response_tarefas = self.make_request('GET', f'/tarefas?projeto_id={projeto_id}')
        
        if not response_tarefas['success']:
            self.log_test("Buscar Tarefas", False, "Erro ao buscar tarefas do projeto", critical=True)
            return False
        
        tarefas = response_tarefas['data']
        if not tarefas or len(tarefas) == 0:
            self.log_test("Tarefas Disponíveis", False, "Nenhuma tarefa encontrada no projeto", critical=True)
            return False
        
        primeira_tarefa = tarefas[0]
        tarefa_id = primeira_tarefa.get('id')
        etapa_original = primeira_tarefa.get('etapa')
        
        print(f"📋 Movendo tarefa: {primeira_tarefa.get('titulo')}")
        print(f"   Etapa original: {etapa_original}")
        
        # Mover tarefa para nova etapa
        nova_etapa = "2 - Ativação do Projeto"
        nova_etapa_encoded = urllib.parse.quote(nova_etapa)
        
        response = self.make_request('PUT', f'/tarefas/{tarefa_id}/mover?nova_etapa={nova_etapa_encoded}')
        
        if response['success']:
            data = response['data']
            if data.get('status') == 'success':
                etapa_anterior = data.get('dados_afetados', {}).get('etapa_anterior')
                etapa_nova = data.get('dados_afetados', {}).get('etapa_nova')
                
                self.log_test("Mover Tarefa", True, 
                            f"Tarefa movida de '{etapa_anterior}' para '{etapa_nova}'")
                
                # Verificar se progresso do projeto foi atualizado
                response_projeto = self.make_request('GET', f'/projetos/{projeto_id}')
                if response_projeto['success']:
                    projeto = response_projeto['data']
                    progresso = projeto.get('progresso', 0)
                    self.log_test("Progresso Atualizado", True, f"Progresso do projeto: {progresso}%")
                
                return True
            else:
                self.log_test("Mover Tarefa", False, f"Status não é success: {data.get('status')}", data, critical=True)
                return False
        else:
            self.log_test("Mover Tarefa", False, 
                        f"Erro ao mover tarefa - Status: {response['status_code']}", response['data'], critical=True)
            return False
    
    def teste_7_avancar_etapa(self):
        """TESTE 7: AVANÇAR ETAPA DO PROJETO"""
        print("\n🔍 TESTE 7: AVANÇAR ETAPA DO PROJETO")
        
        if not self.contratos_criados:
            self.log_test("Avançar Etapa", False, "Nenhum projeto disponível", critical=True)
            return False
        
        primeiro_projeto = self.contratos_criados[0]
        projeto_id = primeiro_projeto['projeto_id']
        cliente = primeiro_projeto['cliente']
        
        print(f"📋 Avançando etapa do projeto: {cliente}")
        
        # Primeiro, marcar todas as tarefas da etapa atual como concluídas
        response_tarefas = self.make_request('GET', f'/tarefas?projeto_id={projeto_id}')
        
        if response_tarefas['success']:
            tarefas = response_tarefas['data']
            tarefas_pendentes = [t for t in tarefas if t.get('status') != 'Concluído']
            
            print(f"📋 Marcando {len(tarefas_pendentes)} tarefas como concluídas...")
            
            for tarefa in tarefas_pendentes:
                tarefa_id = tarefa.get('id')
                update_data = {"status": "Concluído"}
                
                response_update = self.make_request('PUT', f'/tarefas/{tarefa_id}', update_data)
                if response_update['success']:
                    print(f"  ✅ Tarefa concluída: {tarefa.get('titulo')}")
        
        # Agora tentar avançar etapa
        response = self.make_request('POST', f'/projetos/{projeto_id}/avancar-etapa')
        
        if response['success']:
            data = response['data']
            if data.get('status') == 'success':
                etapa_anterior = data.get('dados_afetados', {}).get('etapa_anterior')
                etapa_atual = data.get('dados_afetados', {}).get('etapa_atual')
                novas_tarefas = data.get('dados_afetados', {}).get('novas_tarefas', 0)
                
                self.log_test("Avançar Etapa", True, 
                            f"Etapa avançada de '{etapa_anterior}' para '{etapa_atual}'")
                
                self.log_test("Novas Tarefas Geradas", True, f"{novas_tarefas} novas tarefas foram geradas")
                
                return True
            else:
                self.log_test("Avançar Etapa", False, f"Status não é success: {data.get('status')}", data, critical=True)
                return False
        else:
            self.log_test("Avançar Etapa", False, 
                        f"Erro ao avançar etapa - Status: {response['status_code']}", response['data'], critical=True)
            return False
    
    def teste_8_finalizar_contrato(self):
        """TESTE 8: FINALIZAR CONTRATO"""
        print("\n🔍 TESTE 8: FINALIZAR CONTRATO")
        
        if not self.contratos_criados:
            self.log_test("Finalizar Contrato", False, "Nenhum contrato disponível", critical=True)
            return False
        
        primeiro_contrato = self.contratos_criados[0]
        contrato_id = primeiro_contrato['id']
        cliente = primeiro_contrato['cliente']
        
        print(f"📋 Tentando finalizar contrato: {cliente}")
        
        # Tentar finalizar contrato com tarefas pendentes (deve bloquear)
        response = self.make_request('PUT', f'/contratos/{contrato_id}/finalizar')
        
        if response['success']:
            data = response['data']
            if data.get('status') == 'blocked':
                motivo = data.get('motivo', '')
                if 'tarefa' in motivo.lower() and 'pendente' in motivo.lower():
                    self.log_test("Bloqueio Tarefas Pendentes", True, 
                                f"Sistema bloqueou corretamente: {motivo}")
                    return True
                else:
                    self.log_test("Bloqueio Tarefas Pendentes", False, 
                                f"Motivo do bloqueio não conforme esperado: {motivo}")
                    return False
            elif data.get('status') == 'success':
                self.log_test("Finalização Inesperada", False, 
                            "Contrato foi finalizado mesmo com tarefas pendentes", data)
                return False
            else:
                self.log_test("Finalizar Contrato", False, f"Status inesperado: {data.get('status')}", data)
                return False
        else:
            self.log_test("Finalizar Contrato", False, 
                        f"Erro na requisição - Status: {response['status_code']}", response['data'], critical=True)
            return False
    
    def teste_9_dashboard(self):
        """TESTE 9: DASHBOARD"""
        print("\n🔍 TESTE 9: DASHBOARD")
        
        response = self.make_request('GET', '/dashboard')
        
        if response['success']:
            dashboard = response['data']
            
            # Verificar se todos os KPIs estão corretos
            kpis = dashboard.get('kpis', {})
            
            campos_esperados = [
                'total_projetos', 'percentual_no_prazo', 'projetos_risco_alto', 
                'projetos_risco_medio', 'tarefas_atrasadas_total'
            ]
            
            campos_presentes = all(campo in kpis for campo in campos_esperados)
            
            if campos_presentes:
                self.log_test("KPIs do Dashboard", True, 
                            f"Todos os KPIs presentes - Projetos: {kpis.get('total_projetos')}, "
                            f"No prazo: {kpis.get('percentual_no_prazo')}%, "
                            f"Risco alto: {kpis.get('projetos_risco_alto')}")
                
                # Verificar estrutura de dados
                estrutura_completa = all(key in dashboard for key in [
                    'kpis', 'projetos_por_status', 'tarefas_atrasadas', 'gargalos_responsaveis'
                ])
                
                if estrutura_completa:
                    self.log_test("Estrutura do Dashboard", True, "Estrutura de dados está completa")
                    
                    # Mostrar detalhes
                    projetos_por_status = dashboard.get('projetos_por_status', {})
                    tarefas_atrasadas = dashboard.get('tarefas_atrasadas', [])
                    gargalos = dashboard.get('gargalos_responsaveis', [])
                    
                    print(f"  📊 Status de projetos: {len(projetos_por_status)} tipos")
                    print(f"  📊 Tarefas atrasadas: {len(tarefas_atrasadas)}")
                    print(f"  📊 Gargalos: {len(gargalos)} responsáveis")
                    
                    return True
                else:
                    self.log_test("Estrutura do Dashboard", False, "Estrutura de dados incompleta", dashboard)
                    return False
            else:
                campos_faltando = [c for c in campos_esperados if c not in kpis]
                self.log_test("KPIs do Dashboard", False, f"Campos faltando: {campos_faltando}", dashboard, critical=True)
                return False
        else:
            self.log_test("Dashboard", False, 
                        f"Erro ao acessar dashboard - Status: {response['status_code']}", response['data'], critical=True)
            return False
    
    def teste_10_validacoes_erros(self):
        """TESTE 10: VALIDAÇÕES E ERROS"""
        print("\n🔍 TESTE 10: VALIDAÇÕES E ERROS")
        
        testes_validacao = 0
        testes_sucesso = 0
        
        # 1. Tentar criar contrato com valor negativo
        print("\n📋 Testando contrato com valor negativo...")
        contrato_invalido = {
            "numero_contrato": 999,
            "cliente": "TESTE VALOR NEGATIVO",
            "faculdade": "Teste",
            "semestre": "2025/1",
            "valor": -1000,  # Valor negativo
            "data_inicio": datetime.now().isoformat(),
            "data_fim": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        response = self.make_request('POST', '/contratos', contrato_invalido)
        testes_validacao += 1
        
        if not response['success'] or response['data'].get('status') in ['blocked', 'error']:
            self.log_test("Validação Valor Negativo", True, "Sistema bloqueou valor negativo corretamente")
            testes_sucesso += 1
        else:
            self.log_test("Validação Valor Negativo", False, "Sistema não bloqueou valor negativo", response['data'])
        
        # 2. Tentar criar contrato com data_fim < data_inicio
        print("\n📋 Testando contrato com datas inválidas...")
        hoje = datetime.now()
        contrato_data_invalida = {
            "numero_contrato": 998,
            "cliente": "TESTE DATA INVALIDA",
            "faculdade": "Teste",
            "semestre": "2025/1",
            "valor": 1000,
            "data_inicio": hoje.isoformat(),
            "data_fim": (hoje - timedelta(days=30)).isoformat()  # Data fim anterior ao início
        }
        
        response = self.make_request('POST', '/contratos', contrato_data_invalida)
        testes_validacao += 1
        
        if not response['success'] or response['data'].get('status') in ['blocked', 'error']:
            self.log_test("Validação Data Inválida", True, "Sistema bloqueou datas inválidas corretamente")
            testes_sucesso += 1
        else:
            self.log_test("Validação Data Inválida", False, "Sistema não bloqueou datas inválidas", response['data'])
        
        # 3. Tentar excluir contrato em produção (se houver)
        if self.contratos_criados:
            print("\n📋 Testando exclusão de contrato em produção...")
            contrato_id = self.contratos_criados[0]['id']
            
            response = self.make_request('DELETE', f'/contratos/{contrato_id}')
            testes_validacao += 1
            
            if not response['success'] or response['data'].get('status') == 'blocked':
                motivo = response['data'].get('motivo', '') if response['success'] else 'Erro na requisição'
                self.log_test("Bloqueio Exclusão Produção", True, f"Sistema bloqueou exclusão: {motivo}")
                testes_sucesso += 1
            else:
                self.log_test("Bloqueio Exclusão Produção", False, "Sistema não bloqueou exclusão em produção", response['data'])
        
        # 4. Tentar avançar etapa sem concluir tarefas (se houver projeto com tarefas pendentes)
        if self.contratos_criados:
            print("\n📋 Testando avanço de etapa com tarefas pendentes...")
            projeto_id = self.contratos_criados[-1]['projeto_id']  # Usar último projeto
            
            response = self.make_request('POST', f'/projetos/{projeto_id}/avancar-etapa')
            testes_validacao += 1
            
            if not response['success'] or response['data'].get('status') == 'blocked':
                motivo = response['data'].get('motivo', '') if response['success'] else 'Erro na requisição'
                if 'pendente' in motivo.lower() or 'tarefa' in motivo.lower():
                    self.log_test("Bloqueio Avanço com Pendências", True, f"Sistema bloqueou avanço: {motivo}")
                    testes_sucesso += 1
                else:
                    self.log_test("Bloqueio Avanço com Pendências", False, f"Motivo inesperado: {motivo}")
            else:
                self.log_test("Bloqueio Avanço com Pendências", False, "Sistema não bloqueou avanço com tarefas pendentes", response['data'])
        
        # Resultado final das validações
        if testes_sucesso == testes_validacao and testes_validacao > 0:
            self.log_test("Validações e Erros", True, f"Todas as {testes_validacao} validações funcionaram corretamente")
            return True
        else:
            self.log_test("Validações e Erros", False, 
                        f"Apenas {testes_sucesso}/{testes_validacao} validações funcionaram corretamente")
            return False
    
    def run_all_tests(self):
        """Executa todos os testes conforme especificado"""
        print("🚀 EXECUTANDO BATERIA COMPLETA DE TESTES - SISTEMA IDEIABH")
        print("=" * 70)
        print("Conforme especificado na review request")
        print("=" * 70)
        
        # Lista de testes na ordem especificada
        tests = [
            ("TESTE 1: Health Check", self.teste_1_health_check),
            ("TESTE 2: Limpar Banco e Criar Contratos", self.teste_2_limpar_e_criar_contratos),
            ("TESTE 3: Aprovar Contrato", self.teste_3_aprovar_contrato),
            ("TESTE 4: Visualização da Esteira", self.teste_4_visualizacao_esteira),
            ("TESTE 5: Kanban de Tarefas", self.teste_5_kanban_tarefas),
            ("TESTE 6: Mover Tarefa (Drag and Drop)", self.teste_6_mover_tarefa),
            ("TESTE 7: Avançar Etapa do Projeto", self.teste_7_avancar_etapa),
            ("TESTE 8: Finalizar Contrato", self.teste_8_finalizar_contrato),
            ("TESTE 9: Dashboard", self.teste_9_dashboard),
            ("TESTE 10: Validações e Erros", self.teste_10_validacoes_erros)
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"\n{'='*50}")
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Exceção durante o teste: {str(e)}", critical=True)
                print(f"❌ ERRO CRÍTICO em {test_name}: {str(e)}")
        
        # Relatório final detalhado
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO FINAL DA BATERIA DE TESTES")
        print("=" * 70)
        print(f"Total de testes executados: {self.test_results['total_tests']}")
        print(f"✅ Sucessos: {self.test_results['passed']}")
        print(f"❌ Falhas: {self.test_results['failed']}")
        
        if self.test_results['critical_errors']:
            print(f"\n🚨 ERROS CRÍTICOS ENCONTRADOS ({len(self.test_results['critical_errors'])}):")
            for i, error in enumerate(self.test_results['critical_errors'], 1):
                print(f"{i}. {error}")
        
        if self.test_results['errors']:
            print(f"\n🔍 TODOS OS ERROS ENCONTRADOS:")
            for i, error in enumerate(self.test_results['errors'], 1):
                print(f"{i}. {error}")
        
        success_rate = (self.test_results['passed'] / self.test_results['total_tests']) * 100 if self.test_results['total_tests'] > 0 else 0
        print(f"\n📈 Taxa de sucesso: {success_rate:.1f}%")
        
        # Classificação do resultado
        if success_rate >= 90:
            print("🎉 SISTEMA FUNCIONANDO EXCELENTEMENTE!")
            status = "EXCELENTE"
        elif success_rate >= 80:
            print("✅ SISTEMA FUNCIONANDO ADEQUADAMENTE!")
            status = "BOM"
        elif success_rate >= 60:
            print("⚠️  SISTEMA COM PROBLEMAS MENORES")
            status = "PROBLEMAS MENORES"
        else:
            print("🚨 SISTEMA COM PROBLEMAS CRÍTICOS")
            status = "PROBLEMAS CRÍTICOS"
        
        print(f"\n🏁 STATUS FINAL: {status}")
        print("=" * 70)
        
        return success_rate >= 80


if __name__ == "__main__":
    print("🔧 Configuração da Bateria de Testes:")
    print(f"Base URL: {BASE_URL}")
    print(f"API URL: {API_URL}")
    print()
    
    runner = IDEIABHTestCompleto()
    success = runner.run_all_tests()
    
    exit(0 if success else 1)