#!/usr/bin/env python3
"""
IDEIABH Sistema de Gestão Operacional - Testes Completos
Testa todas as funcionalidades do sistema conforme especificado na review request
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv('/app/frontend/.env')

# Configuração da API
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://govflux-mirror.preview.emergentagent.com')
API_URL = f"{BASE_URL}/api"

class IDEIABHTestRunner:
    def __init__(self):
        self.session = requests.Session()
        self.contratos_criados = []
        self.projetos_criados = []
        self.tarefas_criadas = []
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None):
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
    
    def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Faz requisição para a API"""
        url = f"{API_URL}{endpoint}"
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            
            print(f"🔄 {method} {url} - Status: {response.status_code}")
            
            if response.status_code >= 400:
                print(f"❌ Erro na requisição: {response.text}")
            
            return {
                'status_code': response.status_code,
                'data': response.json() if response.content else {},
                'success': 200 <= response.status_code < 300
            }
        except Exception as e:
            print(f"❌ Erro na requisição {method} {url}: {str(e)}")
            return {
                'status_code': 0,
                'data': {},
                'success': False,
                'error': str(e)
            }
    
    def test_health_check(self):
        """Teste 0: Verificar se a API está funcionando"""
        print("\n🔍 TESTE 0: Health Check da API")
        
        response = self.make_request('GET', '/')
        
        if response['success']:
            data = response['data']
            if data.get('sistema') == 'IDEIABH' and data.get('status') == 'operacional':
                self.log_test("Health Check", True, "API está operacional")
                return True
            else:
                self.log_test("Health Check", False, "Resposta da API não conforme esperado", data)
                return False
        else:
            self.log_test("Health Check", False, f"API não respondeu corretamente - Status: {response['status_code']}")
            return False
    
    def test_criar_contratos(self):
        """TESTE 1: Criar 5 Contratos conforme especificado"""
        print("\n🔍 TESTE 1: Criando 5 Contratos")
        
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
                "faculdade": "Universidade do Estado da Bahia",
                "semestre": "2025/1",
                "valor": 35000,
                "data_inicio": hoje.isoformat(),
                "data_fim": (hoje + timedelta(days=60)).isoformat()
            },
            {
                "numero_contrato": 3,
                "cliente": "ODONTOLOGIA UNIFESO",
                "faculdade": "Centro Universitário Serra dos Órgãos",
                "semestre": "2025/2",
                "valor": 42000,
                "data_inicio": hoje.isoformat(),
                "data_fim": (hoje + timedelta(days=75)).isoformat()
            },
            {
                "numero_contrato": 4,
                "cliente": "ARQUITETURA UNIFACS",
                "faculdade": "Universidade Salvador",
                "semestre": "2025/2",
                "valor": 38000,
                "data_inicio": hoje.isoformat(),
                "data_fim": (hoje + timedelta(days=80)).isoformat()
            },
            {
                "numero_contrato": 5,
                "cliente": "ENFERMAGEM UNIFACS",
                "faculdade": "Universidade Salvador",
                "semestre": "2025/1",
                "valor": 45000,
                "data_inicio": hoje.isoformat(),
                "data_fim": (hoje + timedelta(days=70)).isoformat()
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
                        'numero': contrato_data['numero_contrato']
                    })
                    
                    self.log_test(f"Criar Contrato {i}", True, 
                                f"Contrato criado - ID: {contrato_id}, Projeto: {projeto_id}, Tarefas: {tarefas_criadas}")
                    contratos_criados_com_sucesso += 1
                else:
                    self.log_test(f"Criar Contrato {i}", False, 
                                f"Status não é success: {data.get('status')}", data)
            else:
                self.log_test(f"Criar Contrato {i}", False, 
                            f"Falha na requisição - Status: {response['status_code']}", response['data'])
        
        # Verificar se todos os contratos foram criados
        if contratos_criados_com_sucesso == 5:
            self.log_test("Criação de Contratos", True, f"Todos os 5 contratos foram criados com sucesso")
            return True
        else:
            self.log_test("Criação de Contratos", False, 
                        f"Apenas {contratos_criados_com_sucesso}/5 contratos foram criados")
            return False
    
    def test_verificar_geracao_tarefas(self):
        """TESTE 2: Verificar Geração de Tarefas"""
        print("\n🔍 TESTE 2: Verificando Geração de Tarefas")
        
        if not self.contratos_criados:
            self.log_test("Verificar Tarefas", False, "Nenhum contrato foi criado anteriormente")
            return False
        
        projetos_com_tarefas = 0
        
        for contrato in self.contratos_criados:
            projeto_id = contrato['projeto_id']
            cliente = contrato['cliente']
            
            print(f"\n📋 Verificando projeto do {cliente}")
            
            # Verificar se projeto foi criado
            response_projeto = self.make_request('GET', f'/projetos/{projeto_id}')
            
            if response_projeto['success']:
                projeto = response_projeto['data']
                self.log_test(f"Projeto {cliente}", True, 
                            f"Projeto encontrado - Etapa: {projeto.get('etapa_atual')}")
                
                # Verificar tarefas do projeto
                response_tarefas = self.make_request('GET', f'/tarefas?projeto_id={projeto_id}')
                
                if response_tarefas['success']:
                    tarefas = response_tarefas['data']
                    
                    if isinstance(tarefas, list) and len(tarefas) > 0:
                        # Filtrar tarefas da etapa Lançamento
                        tarefas_lancamento = [t for t in tarefas if t.get('etapa') == '1 - Lançamento do Contrato']
                        
                        self.log_test(f"Tarefas {cliente}", True, 
                                    f"Encontradas {len(tarefas)} tarefas totais, {len(tarefas_lancamento)} da etapa Lançamento")
                        
                        if len(tarefas) > 0:
                            projetos_com_tarefas += 1
                            
                            # Armazenar tarefas para testes posteriores
                            for tarefa in tarefas:
                                self.tarefas_criadas.append({
                                    'id': tarefa.get('id'),
                                    'projeto_id': projeto_id,
                                    'titulo': tarefa.get('titulo'),
                                    'etapa': tarefa.get('etapa'),
                                    'status': tarefa.get('status')
                                })
                    else:
                        self.log_test(f"Tarefas {cliente}", False, 
                                    f"Nenhuma tarefa encontrada para o projeto", tarefas)
                else:
                    self.log_test(f"Tarefas {cliente}", False, 
                                f"Erro ao buscar tarefas - Status: {response_tarefas['status_code']}")
            else:
                self.log_test(f"Projeto {cliente}", False, 
                            f"Projeto não encontrado - Status: {response_projeto['status_code']}")
        
        # Listar todos os projetos
        response_todos_projetos = self.make_request('GET', '/projetos')
        if response_todos_projetos['success']:
            projetos = response_todos_projetos['data']
            self.log_test("Listar Projetos", True, f"Total de projetos no sistema: {len(projetos)}")
        
        # Listar todas as tarefas
        response_todas_tarefas = self.make_request('GET', '/tarefas')
        if response_todas_tarefas['success']:
            tarefas = response_todas_tarefas['data']
            self.log_test("Listar Tarefas", True, f"Total de tarefas no sistema: {len(tarefas)}")
        
        if projetos_com_tarefas == len(self.contratos_criados):
            self.log_test("Geração de Tarefas", True, "Todos os projetos têm tarefas geradas")
            return True
        else:
            self.log_test("Geração de Tarefas", False, 
                        f"Apenas {projetos_com_tarefas}/{len(self.contratos_criados)} projetos têm tarefas")
            return False
    
    def test_avancar_etapas(self):
        """TESTE 3: Avançar Etapas do primeiro projeto"""
        print("\n🔍 TESTE 3: Avançando Etapas do Primeiro Projeto")
        
        if not self.contratos_criados:
            self.log_test("Avançar Etapas", False, "Nenhum contrato disponível para teste")
            return False
        
        # Usar o primeiro projeto
        primeiro_contrato = self.contratos_criados[0]
        projeto_id = primeiro_contrato['projeto_id']
        cliente = primeiro_contrato['cliente']
        
        print(f"\n🎯 Testando avanço de etapas para projeto: {cliente}")
        
        etapas_avancadas = 0
        
        for ciclo in range(3):  # Tentar avançar 3 etapas
            print(f"\n🔄 Ciclo {ciclo + 1}: Concluindo tarefas e avançando etapa")
            
            # 1. Buscar tarefas pendentes do projeto
            response_tarefas = self.make_request('GET', f'/tarefas?projeto_id={projeto_id}')
            
            if not response_tarefas['success']:
                self.log_test(f"Buscar Tarefas Ciclo {ciclo + 1}", False, 
                            f"Erro ao buscar tarefas - Status: {response_tarefas['status_code']}")
                break
            
            tarefas = response_tarefas['data']
            tarefas_pendentes = [t for t in tarefas if t.get('status') != 'Concluído']
            
            print(f"📋 Encontradas {len(tarefas_pendentes)} tarefas pendentes")
            
            # 2. Marcar todas as tarefas pendentes como concluídas
            tarefas_concluidas = 0
            for tarefa in tarefas_pendentes:
                tarefa_id = tarefa.get('id')
                update_data = {
                    "status": "Concluído",
                    "data_conclusao": datetime.now().isoformat()
                }
                
                response_update = self.make_request('PUT', f'/tarefas/{tarefa_id}', update_data)
                
                if response_update['success']:
                    data = response_update['data']
                    if data.get('status') == 'success':
                        tarefas_concluidas += 1
                        print(f"  ✅ Tarefa concluída: {tarefa.get('titulo')}")
                    else:
                        print(f"  ❌ Falha ao concluir tarefa: {data.get('motivo', 'Erro desconhecido')}")
                else:
                    print(f"  ❌ Erro ao atualizar tarefa {tarefa_id}: Status {response_update['status_code']}")
            
            self.log_test(f"Concluir Tarefas Ciclo {ciclo + 1}", tarefas_concluidas > 0, 
                        f"{tarefas_concluidas}/{len(tarefas_pendentes)} tarefas concluídas")
            
            # 3. Tentar avançar etapa
            response_avancar = self.make_request('POST', f'/projetos/{projeto_id}/avancar-etapa')
            
            if response_avancar['success']:
                data = response_avancar['data']
                if data.get('status') == 'success':
                    etapa_anterior = data.get('dados_afetados', {}).get('etapa_anterior')
                    etapa_atual = data.get('dados_afetados', {}).get('etapa_atual')
                    novas_tarefas = data.get('dados_afetados', {}).get('novas_tarefas', 0)
                    
                    self.log_test(f"Avançar Etapa Ciclo {ciclo + 1}", True, 
                                f"Etapa avançada de '{etapa_anterior}' para '{etapa_atual}' - {novas_tarefas} novas tarefas")
                    etapas_avancadas += 1
                else:
                    motivo = data.get('motivo', 'Erro desconhecido')
                    self.log_test(f"Avançar Etapa Ciclo {ciclo + 1}", False, 
                                f"Não foi possível avançar: {motivo}")
                    
                    # Se não conseguiu avançar, pode ser que chegou ao fim ou há algum bloqueio
                    if "última etapa" in motivo.lower() or "não encontrado" in motivo.lower():
                        print(f"ℹ️  Fim do teste de avanço: {motivo}")
                        break
            else:
                self.log_test(f"Avançar Etapa Ciclo {ciclo + 1}", False, 
                            f"Erro na requisição - Status: {response_avancar['status_code']}")
                break
        
        # Verificar estado final do projeto
        response_projeto_final = self.make_request('GET', f'/projetos/{projeto_id}')
        if response_projeto_final['success']:
            projeto = response_projeto_final['data']
            self.log_test("Estado Final do Projeto", True, 
                        f"Etapa atual: {projeto.get('etapa_atual')}, Progresso: {projeto.get('progresso', 0)}%")
        
        if etapas_avancadas > 0:
            self.log_test("Avanço de Etapas", True, f"{etapas_avancadas} etapas foram avançadas com sucesso")
            return True
        else:
            self.log_test("Avanço de Etapas", False, "Nenhuma etapa foi avançada")
            return False
    
    def test_dashboard(self):
        """TESTE 4: Dashboard"""
        print("\n🔍 TESTE 4: Testando Dashboard")
        
        response = self.make_request('GET', '/dashboard')
        
        if response['success']:
            dashboard = response['data']
            
            # Verificar estrutura do dashboard
            kpis = dashboard.get('kpis', {})
            
            campos_esperados = [
                'total_projetos', 'percentual_no_prazo', 'projetos_risco_alto', 
                'projetos_risco_medio', 'tarefas_atrasadas_total'
            ]
            
            campos_presentes = all(campo in kpis for campo in campos_esperados)
            
            if campos_presentes:
                self.log_test("Dashboard KPIs", True, 
                            f"Todos os KPIs presentes - Projetos: {kpis.get('total_projetos')}, "
                            f"No prazo: {kpis.get('percentual_no_prazo')}%, "
                            f"Risco alto: {kpis.get('projetos_risco_alto')}")
                
                # Verificar outras seções
                projetos_por_status = dashboard.get('projetos_por_status', {})
                tarefas_atrasadas = dashboard.get('tarefas_atrasadas', [])
                gargalos = dashboard.get('gargalos_responsaveis', [])
                
                self.log_test("Dashboard Completo", True, 
                            f"Status de projetos: {len(projetos_por_status)} tipos, "
                            f"Tarefas atrasadas: {len(tarefas_atrasadas)}, "
                            f"Gargalos: {len(gargalos)} responsáveis")
                
                return True
            else:
                campos_faltando = [c for c in campos_esperados if c not in kpis]
                self.log_test("Dashboard KPIs", False, 
                            f"Campos faltando nos KPIs: {campos_faltando}", dashboard)
                return False
        else:
            self.log_test("Dashboard", False, 
                        f"Erro ao acessar dashboard - Status: {response['status_code']}", response['data'])
            return False
    
    def test_alertas_notificacoes(self):
        """TESTE 5: Alertas e Notificações"""
        print("\n🔍 TESTE 5: Testando Alertas e Notificações")
        
        if not self.contratos_criados:
            self.log_test("Alertas", False, "Nenhum projeto disponível para testar alertas")
            return False
        
        alertas_testados = 0
        
        for contrato in self.contratos_criados:
            projeto_id = contrato['projeto_id']
            cliente = contrato['cliente']
            
            print(f"\n🚨 Testando alertas para projeto: {cliente}")
            
            # Buscar alertas do projeto
            response_alertas = self.make_request('GET', f'/alertas/{projeto_id}')
            
            if response_alertas['success']:
                alertas = response_alertas['data']
                
                if isinstance(alertas, list):
                    self.log_test(f"Alertas {cliente}", True, 
                                f"Sistema de alertas funcionando - {len(alertas)} alertas encontrados")
                    alertas_testados += 1
                    
                    # Mostrar detalhes dos alertas se houver
                    for alerta in alertas:
                        print(f"  🔔 Alerta: {alerta.get('tipo')} - {alerta.get('mensagem')}")
                else:
                    self.log_test(f"Alertas {cliente}", False, 
                                f"Resposta de alertas não é uma lista", alertas)
            else:
                self.log_test(f"Alertas {cliente}", False, 
                            f"Erro ao buscar alertas - Status: {response_alertas['status_code']}")
        
        # Testar sistema de notificações (se houver usuários)
        # Primeiro, tentar listar usuários
        response_users = self.make_request('GET', '/admin/users')
        
        if response_users['success']:
            users = response_users['data']
            self.log_test("Sistema de Usuários", True, f"Sistema de usuários funcionando - {len(users)} usuários")
            
            # Se houver usuários, testar notificações
            if users and len(users) > 0:
                primeiro_user = users[0]
                user_id = primeiro_user.get('id')
                
                if user_id:
                    response_notif = self.make_request('GET', f'/notificacoes/{user_id}')
                    
                    if response_notif['success']:
                        notificacoes = response_notif['data']
                        self.log_test("Sistema de Notificações", True, 
                                    f"Sistema de notificações funcionando - {len(notificacoes)} notificações")
                    else:
                        self.log_test("Sistema de Notificações", False, 
                                    f"Erro ao buscar notificações - Status: {response_notif['status_code']}")
        else:
            self.log_test("Sistema de Usuários", False, 
                        f"Erro ao acessar usuários - Status: {response_users['status_code']}")
        
        if alertas_testados > 0:
            self.log_test("Sistema de Alertas", True, f"Sistema de alertas testado em {alertas_testados} projetos")
            return True
        else:
            self.log_test("Sistema de Alertas", False, "Nenhum projeto teve alertas testados com sucesso")
            return False
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print("🚀 INICIANDO TESTES COMPLETOS DO SISTEMA IDEIABH")
        print("=" * 60)
        
        # Executar testes em sequência
        tests = [
            ("Health Check", self.test_health_check),
            ("Criar Contratos", self.test_criar_contratos),
            ("Verificar Geração de Tarefas", self.test_verificar_geracao_tarefas),
            ("Avançar Etapas", self.test_avancar_etapas),
            ("Dashboard", self.test_dashboard),
            ("Alertas e Notificações", self.test_alertas_notificacoes)
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Exceção durante o teste: {str(e)}")
        
        # Relatório final
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL DOS TESTES")
        print("=" * 60)
        print(f"Total de testes: {self.test_results['total_tests']}")
        print(f"✅ Sucessos: {self.test_results['passed']}")
        print(f"❌ Falhas: {self.test_results['failed']}")
        
        if self.test_results['failed'] > 0:
            print(f"\n🔍 RESUMO DOS ERROS:")
            for i, error in enumerate(self.test_results['errors'], 1):
                print(f"{i}. {error}")
        
        success_rate = (self.test_results['passed'] / self.test_results['total_tests']) * 100 if self.test_results['total_tests'] > 0 else 0
        print(f"\n📈 Taxa de sucesso: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 SISTEMA FUNCIONANDO ADEQUADAMENTE!")
        elif success_rate >= 60:
            print("⚠️  SISTEMA COM PROBLEMAS MENORES")
        else:
            print("🚨 SISTEMA COM PROBLEMAS CRÍTICOS")
        
        return success_rate >= 80


if __name__ == "__main__":
    print("🔧 Configuração:")
    print(f"Base URL: {BASE_URL}")
    print(f"API URL: {API_URL}")
    print()
    
    runner = IDEIABHTestRunner()
    success = runner.run_all_tests()
    
    exit(0 if success else 1)