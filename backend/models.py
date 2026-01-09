from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
import uuid
import hashlib

# Enums para Status
class UserRole(str, Enum):
    ADMIN = "Administrador"
    ATENDIMENTO = "Atendimento"
    CRIACAO = "Criação"
    PRE_PRODUCAO = "Pré-Produção"
    PRODUCAO = "Produção"
    REVISAO = "Revisão de Texto"
    CLIENTE = "Cliente"

# Enums para Status
class ContratoStatus(str, Enum):
    ATIVO = "Ativo"
    EM_ANDAMENTO = "Em Andamento"
    FINALIZADO = "Finalizado"
    ENCERRADO = "Encerrado"

class EtapaProjeto(str, Enum):
    LANCAMENTO = "1 - Lançamento do Contrato"
    ATIVACAO = "2 - Ativação do Projeto"
    REVISAO_TEXTO = "3 - Revisão de Texto / Preparação das Fotos"
    CRIACAO_1_2 = "4 - Criação (1ª e 2ª AP)"
    CONFERENCIA = "5 - Conferência do Layout"
    AJUSTE_LAYOUT = "5.1 - Ajuste Layout"
    CRIACAO_3_4 = "6 - Criação (3ª e 4ª AP)"
    APROVACAO_FINAL = "7 - Aprovação Final (Criação)"
    PLANEJAMENTO_PRODUCAO = "8 - Planejamento de Produção"
    PRE_PRODUCAO = "9 - Pré-Produção"
    PRODUCAO = "10 - Produção"
    QUALIDADE = "11 - Qualidade"
    ENTREGA = "12 - Entrega"
    POS_VENDAS = "13 - Pós-Vendas"
    ENCERRADO = "14 - Contrato Encerrado"

class MacroEtapa(str, Enum):
    ATENDIMENTO = "Atendimento"
    CLIENTE = "Cliente"
    PREPARACAO = "Preparação"
    CRIACAO = "Criação"
    PRE_PRODUCAO = "Pré-Produção"
    PRODUCAO = "Produção"
    POS_VENDAS = "Pós-Vendas"

class TarefaStatus(str, Enum):
    PENDENTE = "Pendente"
    EM_ANDAMENTO = "Em Andamento"
    AGUARDANDO = "Aguardando"
    CONCLUIDO = "Concluído"
    ATRASADO = "Atrasado"

class NivelRisco(str, Enum):
    BAIXO = "Baixo"
    MEDIO = "Médio"
    ALTO = "Alto"

# Models
class Log(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    acao: str
    usuario: str = "Sistema"
    detalhes: dict = {}

class Contrato(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    numero_contrato: int
    cliente: str
    faculdade: str
    semestre: str  # Ex: "2025/1"
    valor: float
    data_inicio: datetime
    data_fim: datetime
    status: ContratoStatus = ContratoStatus.ATIVO
    projeto_id: Optional[str] = None
    logs: List[Log] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('valor')
    def validar_valor(cls, v):
        if v <= 0:
            raise ValueError('Valor deve ser maior que zero')
        return v

    @validator('data_fim')
    def validar_datas(cls, v, values):
        if 'data_inicio' in values and v <= values['data_inicio']:
            raise ValueError('Data fim deve ser posterior à data início')
        return v

class ContratoCreate(BaseModel):
    numero_contrato: int
    cliente: str
    faculdade: str
    semestre: str
    valor: float
    data_inicio: datetime
    data_fim: datetime

class ContratoUpdate(BaseModel):
    cliente: Optional[str] = None
    faculdade: Optional[str] = None
    semestre: Optional[str] = None
    valor: Optional[float] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    status: Optional[ContratoStatus] = None

class Projeto(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contrato_id: str
    etapa_atual: EtapaProjeto = EtapaProjeto.LANCAMENTO
    macro_etapa: MacroEtapa = MacroEtapa.ATENDIMENTO
    progresso: float = 0.0
    risco: NivelRisco = NivelRisco.BAIXO
    data_entrega: datetime
    responsavel_atendimento: str = "Keyla Nascimento"
    responsavel_designer: str = "Marcos Letro"
    logs: List[Log] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProjetoUpdate(BaseModel):
    etapa_atual: Optional[EtapaProjeto] = None
    macro_etapa: Optional[MacroEtapa] = None
    risco: Optional[NivelRisco] = None
    responsavel_atendimento: Optional[str] = None
    responsavel_designer: Optional[str] = None

class Tarefa(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    projeto_id: str
    etapa: EtapaProjeto
    macro_etapa: MacroEtapa
    numero: int  # Número da atividade na esteira
    atividade: str  # Nome da atividade
    setor: str  # Setor responsável
    titulo: str
    descricao: Optional[str] = None
    responsavel: str
    prazo: datetime
    data_conclusao: Optional[datetime] = None
    status: TarefaStatus = TarefaStatus.PENDENTE
    dependencias: List[str] = []
    critica: bool = False
    logs: List[Log] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TarefaCreate(BaseModel):
    projeto_id: str
    etapa: EtapaProjeto
    macro_etapa: MacroEtapa
    numero: int
    atividade: str
    setor: str
    titulo: str
    descricao: Optional[str] = None
    responsavel: str
    prazo: datetime
    dependencias: List[str] = []
    critica: bool = False

class TarefaUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    responsavel: Optional[str] = None
    prazo: Optional[datetime] = None
    status: Optional[TarefaStatus] = None
    data_conclusao: Optional[datetime] = None
    dependencias: Optional[List[str]] = None

class Alerta(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: str
    projeto_id: str
    mensagem: str
    nivel: NivelRisco
    acao_sugerida: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolvido: bool = False

class Notificacao(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    destinatario: str
    assunto: str
    corpo: str
    tipo: str
    enviado: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OperacaoResponse(BaseModel):
    status: str  # success, blocked, error
    acao_executada: str
    motivo: Optional[str] = None
    dados_afetados: dict = {}
    alertas: List[str] = []
    emails_disparados: List[str] = []
    logs: List[dict] = []

# User e Permissões
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    email: str
    senha_hash: str
    role: UserRole = UserRole.ATENDIMENTO
    ativo: bool = True
    permissoes: Dict[str, bool] = {
        "dashboard": True,
        "contratos_visualizar": True,
        "contratos_criar": False,
        "contratos_editar": False,
        "contratos_excluir": False,
        "contratos_aprovar": False,
        "contratos_finalizar": False,
        "projetos_visualizar": True,
        "projetos_avancar": False,
        "tarefas_visualizar": True,
        "tarefas_criar": False,
        "tarefas_editar": False,
        "tarefas_concluir": False,
        "tarefas_mover": False,
        "admin": False
    }
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    nome: str
    email: str
    senha: str
    role: UserRole = UserRole.ATENDIMENTO

class UserUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    senha: Optional[str] = None
    role: Optional[UserRole] = None
    ativo: Optional[bool] = None
    permissoes: Optional[Dict[str, bool]] = None

class UserLogin(BaseModel):
    email: str
    senha: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class NotificacaoUsuario(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tipo: str  # tarefa_atrasada, nova_tarefa, aprovacao_necessaria, etc
    titulo: str
    mensagem: str
    link: Optional[str] = None
    lida: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Definição da Esteira Completa
ESTEIRA_COMPLETA = [
    {"numero": 1, "atividade": "Lançamento do Contrato", "setor": "Atendimento", "etapa": EtapaProjeto.LANCAMENTO, "macro": MacroEtapa.ATENDIMENTO},
    {"numero": 2, "atividade": "Apresentação do Projeto", "setor": "Atendimento", "etapa": EtapaProjeto.ATIVACAO, "macro": MacroEtapa.ATENDIMENTO},
    {"numero": 3, "atividade": "Agendamento de Criação", "setor": "Atendimento", "etapa": EtapaProjeto.ATIVACAO, "macro": MacroEtapa.ATENDIMENTO},
    {"numero": 4, "atividade": "Reunião de Criação", "setor": "Criação", "etapa": EtapaProjeto.ATIVACAO, "macro": MacroEtapa.ATENDIMENTO},
    {"numero": 5, "atividade": "Envio de Fotos e Textos", "setor": "Cliente", "etapa": EtapaProjeto.REVISAO_TEXTO, "macro": MacroEtapa.CLIENTE},
    {"numero": 6, "atividade": "Revisão de Texto", "setor": "Revisão de Texto", "etapa": EtapaProjeto.REVISAO_TEXTO, "macro": MacroEtapa.PREPARACAO},
    {"numero": 7, "atividade": "Preparação de Fotos", "setor": "Pré-Produção", "etapa": EtapaProjeto.REVISAO_TEXTO, "macro": MacroEtapa.PREPARACAO},
    {"numero": 8, "atividade": "Criação", "setor": "Criação", "etapa": EtapaProjeto.CRIACAO_1_2, "macro": MacroEtapa.CRIACAO},
    {"numero": 9, "atividade": "1ª Apresentação do Convite", "setor": "Criação", "etapa": EtapaProjeto.CRIACAO_1_2, "macro": MacroEtapa.CRIACAO},
    {"numero": 10, "atividade": "1º Ajuste", "setor": "Criação", "etapa": EtapaProjeto.CRIACAO_1_2, "macro": MacroEtapa.CRIACAO},
    {"numero": 11, "atividade": "2ª Apresentação do Convite", "setor": "Criação", "etapa": EtapaProjeto.CRIACAO_1_2, "macro": MacroEtapa.CRIACAO},
    {"numero": 12, "atividade": "2º Ajuste", "setor": "Criação", "etapa": EtapaProjeto.CRIACAO_1_2, "macro": MacroEtapa.CRIACAO},
    {"numero": 13, "atividade": "Conferência do Layout", "setor": "Atendimento", "etapa": EtapaProjeto.CONFERENCIA, "macro": MacroEtapa.CRIACAO},
    {"numero": 14, "atividade": "Ajuste Layout", "setor": "Criação", "etapa": EtapaProjeto.AJUSTE_LAYOUT, "macro": MacroEtapa.CRIACAO},
    {"numero": 15, "atividade": "3ª Apresentação do Convite", "setor": "Criação", "etapa": EtapaProjeto.CRIACAO_3_4, "macro": MacroEtapa.CRIACAO},
    {"numero": 16, "atividade": "3º Ajuste", "setor": "Criação", "etapa": EtapaProjeto.CRIACAO_3_4, "macro": MacroEtapa.CRIACAO},
    {"numero": 17, "atividade": "4ª Apresentação do Convite", "setor": "Criação", "etapa": EtapaProjeto.CRIACAO_3_4, "macro": MacroEtapa.CRIACAO},
    {"numero": 18, "atividade": "4º Ajuste", "setor": "Criação", "etapa": EtapaProjeto.CRIACAO_3_4, "macro": MacroEtapa.CRIACAO},
    {"numero": 19, "atividade": "Aprovação Final", "setor": "Cliente", "etapa": EtapaProjeto.APROVACAO_FINAL, "macro": MacroEtapa.CRIACAO},
    {"numero": 20, "atividade": "Planejamento de Produção", "setor": "Produção", "etapa": EtapaProjeto.PLANEJAMENTO_PRODUCAO, "macro": MacroEtapa.PRE_PRODUCAO},
    {"numero": 21, "atividade": "Saída de Convite", "setor": "Pré-Produção", "etapa": EtapaProjeto.PRE_PRODUCAO, "macro": MacroEtapa.PRE_PRODUCAO},
    {"numero": 22, "atividade": "Impressão", "setor": "Pré-Produção", "etapa": EtapaProjeto.PRE_PRODUCAO, "macro": MacroEtapa.PRE_PRODUCAO},
    {"numero": 23, "atividade": "Produção", "setor": "Produção", "etapa": EtapaProjeto.PRODUCAO, "macro": MacroEtapa.PRODUCAO},
    {"numero": 24, "atividade": "Qualidade", "setor": "Produção", "etapa": EtapaProjeto.QUALIDADE, "macro": MacroEtapa.PRODUCAO},
    {"numero": 25, "atividade": "Entrega", "setor": "Produção", "etapa": EtapaProjeto.ENTREGA, "macro": MacroEtapa.PRODUCAO},
]
