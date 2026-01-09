from typing import List
from datetime import datetime, timedelta
from models import (
    Tarefa, EtapaProjeto, MacroEtapa, TarefaStatus,
    NotificacaoUsuario, ESTEIRA_COMPLETA
)
import logging

logger = logging.getLogger(__name__)

class GeradorTarefas:
    """Gera tarefas progressivamente conforme o projeto avança"""
    
    def __init__(self, db):
        self.db = db
    
    async def gerar_tarefas_etapa(self, projeto_id: str, etapa: EtapaProjeto, data_base: datetime) -> List[Tarefa]:
        """
        Gera as tarefas de uma etapa específica
        
        Lógica: Ao avançar para uma etapa, criar as atividades dessa etapa
        """
        tarefas_criadas = []
        
        # Filtrar atividades da esteira para esta etapa
        atividades_etapa = [a for a in ESTEIRA_COMPLETA if a['etapa'] == etapa]
        
        if not atividades_etapa:
            return tarefas_criadas
        
        # Calcular prazo baseado na etapa
        dias_prazo = self._calcular_prazo_etapa(etapa)
        
        for i, atividade in enumerate(atividades_etapa):
            prazo = data_base + timedelta(days=dias_prazo + i)
            
            tarefa = Tarefa(
                projeto_id=projeto_id,
                etapa=atividade['etapa'],
                macro_etapa=atividade['macro'],
                numero=atividade['numero'],
                atividade=atividade['atividade'],
                setor=atividade['setor'],
                titulo=atividade['atividade'],
                descricao=f"Etapa: {atividade['etapa'].value}",
                responsavel=self._definir_responsavel(atividade['setor']),
                prazo=prazo,
                status=TarefaStatus.PENDENTE,
                critica=self._definir_criticidade(atividade['numero'])
            )
            
            tarefa_dict = tarefa.dict()
            tarefa_dict['etapa'] = tarefa_dict['etapa'].value
            tarefa_dict['macro_etapa'] = tarefa_dict['macro_etapa'].value
            tarefa_dict['status'] = tarefa_dict['status'].value
            tarefa_dict['prazo'] = tarefa_dict['prazo'].isoformat()
            tarefa_dict['created_at'] = tarefa_dict['created_at'].isoformat()
            
            await self.db.tarefas.insert_one(tarefa_dict)
            tarefas_criadas.append(tarefa)
            
            logger.info(f"Tarefa criada: {tarefa.titulo} - Prazo: {tarefa.prazo}")
        
        return tarefas_criadas
    
    def _calcular_prazo_etapa(self, etapa: EtapaProjeto) -> int:
        """Define quantos dias para cada etapa"""
        prazos = {
            EtapaProjeto.LANCAMENTO: 1,
            EtapaProjeto.ATIVACAO: 3,
            EtapaProjeto.REVISAO_TEXTO: 5,
            EtapaProjeto.CRIACAO_1_2: 7,
            EtapaProjeto.CONFERENCIA: 2,
            EtapaProjeto.AJUSTE_LAYOUT: 2,
            EtapaProjeto.CRIACAO_3_4: 5,
            EtapaProjeto.APROVACAO_FINAL: 2,
            EtapaProjeto.PLANEJAMENTO_PRODUCAO: 3,
            EtapaProjeto.PRE_PRODUCAO: 5,
            EtapaProjeto.PRODUCAO: 7,
            EtapaProjeto.QUALIDADE: 2,
            EtapaProjeto.ENTREGA: 1,
        }
        return prazos.get(etapa, 3)
    
    def _definir_responsavel(self, setor: str) -> str:
        """Define responsável baseado no setor"""
        responsaveis = {
            "Atendimento": "Keyla Nascimento",
            "Criação": "Marcos Letro",
            "Cliente": "Cliente",
            "Revisão de Texto": "Larissa Elias",
            "Pré-Produção": "Carlos Augusto",
            "Produção": "Ricardo Mayrink"
        }
        return responsaveis.get(setor, "Sistema")
    
    def _definir_criticidade(self, numero: int) -> bool:
        """Define se a tarefa é crítica baseada no número"""
        # Tarefas críticas: aprovações, reuniões principais, entregas
        tarefas_criticas = [1, 4, 8, 13, 19, 20, 23, 25]
        return numero in tarefas_criticas


class GeradorNotificacoes:
    """Gera notificações para usuários"""
    
    def __init__(self, db):
        self.db = db
    
    async def notificar_tarefa_atribuida(self, tarefa: Tarefa):
        """Notifica quando uma tarefa é atribuída"""
        # Buscar usuário pelo nome do responsável
        user = await self.db.users.find_one({"nome": tarefa.responsavel})
        
        if not user:
            return
        
        notificacao = NotificacaoUsuario(
            user_id=user['id'],
            tipo="nova_tarefa",
            titulo="Nova tarefa atribuída",
            mensagem=f"Você foi designado para: {tarefa.titulo}",
            link=f"/tarefas?tarefa_id={tarefa.id}"
        )
        
        notif_dict = notificacao.dict()
        notif_dict['created_at'] = notif_dict['created_at'].isoformat()
        
        await self.db.notificacoes_usuarios.insert_one(notif_dict)
        logger.info(f"Notificação criada para {tarefa.responsavel}")
    
    async def notificar_tarefa_atrasada(self, tarefa: Tarefa, dias_atraso: int):
        """Notifica quando uma tarefa está atrasada"""
        user = await self.db.users.find_one({"nome": tarefa.responsavel})
        
        if not user:
            return
        
        notificacao = NotificacaoUsuario(
            user_id=user['id'],
            tipo="tarefa_atrasada",
            titulo="⚠️ Tarefa atrasada!",
            mensagem=f"{tarefa.titulo} está atrasada em {dias_atraso} dia(s)",
            link=f"/tarefas?tarefa_id={tarefa.id}"
        )
        
        notif_dict = notificacao.dict()
        notif_dict['created_at'] = notif_dict['created_at'].isoformat()
        
        await self.db.notificacoes_usuarios.insert_one(notif_dict)
        logger.info(f"Notificação de atraso enviada para {tarefa.responsavel}")
    
    async def notificar_aprovacao_necessaria(self, projeto_id: str, etapa: str):
        """Notifica quando uma aprovação é necessária"""
        # Notificar todos os administradores
        admins = await self.db.users.find({"role": "Administrador"}).to_list(100)
        
        for admin in admins:
            notificacao = NotificacaoUsuario(
                user_id=admin['id'],
                tipo="aprovacao_necessaria",
                titulo="Aprovação necessária",
                mensagem=f"Projeto requer aprovação na etapa: {etapa}",
                link=f"/projetos?projeto_id={projeto_id}"
            )
            
            notif_dict = notificacao.dict()
            notif_dict['created_at'] = notif_dict['created_at'].isoformat()
            
            await self.db.notificacoes_usuarios.insert_one(notif_dict)


class CalculadorCriticidade:
    """Calcula criticidade baseado no prazo restante"""
    
    @staticmethod
    def calcular_criticidade(prazo: datetime, data_entrega: datetime) -> str:
        """
        Retorna nível de criticidade baseado nos dias restantes
        
        - 0-7 dias: CRÍTICO
        - 8-15 dias: ATENÇÃO
        - 16+ dias: NORMAL
        """
        agora = datetime.utcnow()
        dias_restantes = (data_entrega - agora).days
        
        if dias_restantes <= 7:
            return "CRÍTICO"
        elif dias_restantes <= 15:
            return "ATENÇÃO"
        else:
            return "NORMAL"
    
    @staticmethod
    def calcular_dias_restantes(data_entrega: datetime) -> int:
        """Calcula quantos dias faltam para a entrega"""
        agora = datetime.utcnow()
        return max(0, (data_entrega - agora).days)
