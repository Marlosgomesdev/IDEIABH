from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from models import (
    Contrato, Projeto, Tarefa, Alerta, Notificacao,
    ContratoStatus, EtapaProjeto, TarefaStatus, NivelRisco,
    Log, OperacaoResponse
)
import logging

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """Motor de Workflow e Governança do IDEIABH"""
    
    def __init__(self, db):
        self.db = db
    
    # ============ VALIDAÇÕES DE FLUXO ============
    
    def validar_transicao_etapa(self, projeto: Projeto, nova_etapa: EtapaProjeto) -> tuple[bool, Optional[str]]:
        """Valida se a transição de etapa é permitida"""
        
        etapas_ordem = [EtapaProjeto.CRIACAO, EtapaProjeto.PRE_PRODUCAO, EtapaProjeto.PRODUCAO]
        
        if projeto.etapa_atual == nova_etapa:
            return False, "Projeto já está nesta etapa"
        
        idx_atual = etapas_ordem.index(projeto.etapa_atual)
        idx_nova = etapas_ordem.index(nova_etapa)
        
        # Não pode pular etapas
        if idx_nova > idx_atual + 1:
            return False, f"Não é possível pular etapas. Etapa atual: {projeto.etapa_atual.value}"
        
        # Não pode voltar etapas
        if idx_nova < idx_atual:
            return False, "Não é possível voltar para etapas anteriores"
        
        # Validações específicas
        if nova_etapa == EtapaProjeto.PRE_PRODUCAO:
            # Verificar se todas as tarefas de Criação estão concluídas
            tarefas_criacao = self.db.tarefas.find({
                "projeto_id": projeto.id,
                "etapa": EtapaProjeto.CRIACAO.value
            })
            
            for tarefa in tarefas_criacao:
                if tarefa.get('status') != TarefaStatus.CONCLUIDO.value:
                    return False, "Todas as tarefas da etapa Criação devem estar concluídas"
        
        if nova_etapa == EtapaProjeto.PRODUCAO:
            # Verificar se todas as tarefas de Pré-Produção estão concluídas
            tarefas_pre = self.db.tarefas.find({
                "projeto_id": projeto.id,
                "etapa": EtapaProjeto.PRE_PRODUCAO.value
            })
            
            for tarefa in tarefas_pre:
                if tarefa.get('status') != TarefaStatus.CONCLUIDO.value:
                    return False, "Todas as tarefas da etapa Pré-Produção devem estar concluídas"
        
        return True, None
    
    def validar_dependencias_tarefa(self, tarefa: Tarefa) -> tuple[bool, Optional[str]]:
        """Valida se todas as dependências de uma tarefa estão concluídas"""
        
        if not tarefa.dependencias:
            return True, None
        
        for dep_id in tarefa.dependencias:
            dep_tarefa = self.db.tarefas.find_one({"id": dep_id})
            
            if not dep_tarefa:
                return False, f"Dependência {dep_id} não encontrada"
            
            if dep_tarefa.get('status') != TarefaStatus.CONCLUIDO.value:
                return False, f"Tarefa dependente '{dep_tarefa.get('titulo')}' ainda não foi concluída"
        
        return True, None
    
    # ============ CÁLCULO DE PROGRESSO E RISCO ============
    
    async def calcular_progresso_projeto(self, projeto_id: str) -> float:
        """Calcula o progresso do projeto baseado nas tarefas"""
        
        tarefas = await self.db.tarefas.find({"projeto_id": projeto_id}).to_list(1000)
        
        if not tarefas:
            return 0.0
        
        concluidas = sum(1 for t in tarefas if t.get('status') == TarefaStatus.CONCLUIDO.value)
        total = len(tarefas)
        
        return round((concluidas / total) * 100, 2)
    
    async def avaliar_risco_projeto(self, projeto_id: str) -> NivelRisco:
        """Avalia o nível de risco do projeto"""
        
        tarefas = await self.db.tarefas.find({"projeto_id": projeto_id}).to_list(1000)
        projeto = await self.db.projetos.find_one({"id": projeto_id})
        
        if not projeto:
            return NivelRisco.BAIXO
        
        agora = datetime.utcnow()
        pontos_risco = 0
        
        # Verificar tarefas atrasadas
        tarefas_atrasadas = 0
        tarefas_criticas_atrasadas = 0
        
        for tarefa in tarefas:
            if tarefa.get('status') != TarefaStatus.CONCLUIDO.value:
                prazo = tarefa.get('prazo')
                if isinstance(prazo, str):
                    prazo = datetime.fromisoformat(prazo.replace('Z', '+00:00'))
                
                if prazo < agora:
                    tarefas_atrasadas += 1
                    if tarefa.get('critica', False):
                        tarefas_criticas_atrasadas += 1
                        pontos_risco += 3
                    else:
                        pontos_risco += 1
        
        # Verificar proximidade da data de entrega
        data_entrega = projeto.get('data_entrega')
        if isinstance(data_entrega, str):
            data_entrega = datetime.fromisoformat(data_entrega.replace('Z', '+00:00'))
        
        dias_restantes = (data_entrega - agora).days
        
        if dias_restantes < 7:
            pontos_risco += 2
        elif dias_restantes < 15:
            pontos_risco += 1
        
        # Verificar etapa parada (sem progresso recente)
        # TODO: Implementar verificação de última atualização
        
        # Classificar risco
        if pontos_risco >= 5 or tarefas_criticas_atrasadas > 0:
            return NivelRisco.ALTO
        elif pontos_risco >= 2:
            return NivelRisco.MEDIO
        else:
            return NivelRisco.BAIXO
    
    # ============ GERAÇÃO AUTOMÁTICA DE TAREFAS ============
    
    async def gerar_tarefas_criacao(self, projeto_id: str, contrato_id: str) -> List[Tarefa]:
        """Gera tarefas padrão da etapa Criação"""
        
        contrato = await self.db.contratos.find_one({"id": contrato_id})
        if not contrato:
            return []
        
        data_entrega = contrato.get('data_fim')
        if isinstance(data_entrega, str):
            data_entrega = datetime.fromisoformat(data_entrega.replace('Z', '+00:00'))
        
        # Calcular prazos regressivos
        prazo_briefing = data_entrega - timedelta(days=45)
        prazo_analise = data_entrega - timedelta(days=40)
        prazo_planejamento = data_entrega - timedelta(days=35)
        prazo_aprovacao = data_entrega - timedelta(days=30)
        
        tarefas_padrao = [
            {
                "projeto_id": projeto_id,
                "etapa": EtapaProjeto.CRIACAO.value,
                "titulo": "Briefing Inicial com Cliente",
                "descricao": "Reunião inicial para coleta de requisitos e expectativas",
                "responsavel": "Gerente de Projetos",
                "prazo": prazo_briefing,
                "status": TarefaStatus.PENDENTE.value,
                "dependencias": [],
                "critica": True
            },
            {
                "projeto_id": projeto_id,
                "etapa": EtapaProjeto.CRIACAO.value,
                "titulo": "Análise de Viabilidade",
                "descricao": "Análise técnica e financeira do projeto",
                "responsavel": "Analista Técnico",
                "prazo": prazo_analise,
                "status": TarefaStatus.PENDENTE.value,
                "dependencias": [],
                "critica": True
            },
            {
                "projeto_id": projeto_id,
                "etapa": EtapaProjeto.CRIACAO.value,
                "titulo": "Planejamento de Execução",
                "descricao": "Definição de cronograma, recursos e entregas",
                "responsavel": "Gerente de Projetos",
                "prazo": prazo_planejamento,
                "status": TarefaStatus.PENDENTE.value,
                "dependencias": [],
                "critica": True
            },
            {
                "projeto_id": projeto_id,
                "etapa": EtapaProjeto.CRIACAO.value,
                "titulo": "Aprovação do Plano",
                "descricao": "Aprovação formal do planejamento pelo cliente",
                "responsavel": "Gerente de Projetos",
                "prazo": prazo_aprovacao,
                "status": TarefaStatus.PENDENTE.value,
                "dependencias": [],
                "critica": True
            }
        ]
        
        tarefas_criadas = []
        for tarefa_data in tarefas_padrao:
            from models import Tarefa
            tarefa = Tarefa(**tarefa_data)
            tarefa_dict = tarefa.dict()
            tarefa_dict['prazo'] = tarefa_dict['prazo'].isoformat()
            tarefa_dict['created_at'] = tarefa_dict['created_at'].isoformat()
            
            await self.db.tarefas.insert_one(tarefa_dict)
            tarefas_criadas.append(tarefa)
        
        return tarefas_criadas
    
    # ============ DETECÇÃO DE ALERTAS ============
    
    async def detectar_alertas(self, projeto_id: str) -> List[Alerta]:
        """Detecta problemas e gera alertas"""
        
        alertas = []
        tarefas = await self.db.tarefas.find({"projeto_id": projeto_id}).to_list(1000)
        projeto = await self.db.projetos.find_one({"id": projeto_id})
        
        if not projeto:
            return alertas
        
        agora = datetime.utcnow()
        
        # Detectar tarefas atrasadas
        for tarefa in tarefas:
            if tarefa.get('status') != TarefaStatus.CONCLUIDO.value:
                prazo = tarefa.get('prazo')
                if isinstance(prazo, str):
                    prazo = datetime.fromisoformat(prazo.replace('Z', '+00:00'))
                
                if prazo < agora:
                    dias_atraso = (agora - prazo).days
                    alerta = Alerta(
                        tipo="tarefa_atrasada",
                        projeto_id=projeto_id,
                        mensagem=f"Tarefa '{tarefa.get('titulo')}' está atrasada em {dias_atraso} dia(s)",
                        nivel=NivelRisco.ALTO if tarefa.get('critica') else NivelRisco.MEDIO,
                        acao_sugerida=f"Contatar {tarefa.get('responsavel')} imediatamente"
                    )
                    alertas.append(alerta)
        
        # Detectar risco alto
        risco = await self.avaliar_risco_projeto(projeto_id)
        if risco == NivelRisco.ALTO:
            alerta = Alerta(
                tipo="risco_alto",
                projeto_id=projeto_id,
                mensagem="Projeto classificado com RISCO ALTO",
                nivel=NivelRisco.ALTO,
                acao_sugerida="Reunião emergencial com equipe e cliente"
            )
            alertas.append(alerta)
        
        return alertas
    
    # ============ NOTIFICAÇÕES ============
    
    async def criar_notificacao(self, destinatario: str, assunto: str, corpo: str, tipo: str) -> Notificacao:
        """Cria uma notificação (preparado para envio de e-mail)"""
        
        notificacao = Notificacao(
            destinatario=destinatario,
            assunto=assunto,
            corpo=corpo,
            tipo=tipo
        )
        
        notif_dict = notificacao.dict()
        notif_dict['created_at'] = notif_dict['created_at'].isoformat()
        
        await self.db.notificacoes.insert_one(notif_dict)
        
        logger.info(f"Notificação criada: {assunto} para {destinatario}")
        
        return notificacao
