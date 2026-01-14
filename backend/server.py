from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from models import (
    Contrato, ContratoCreate, ContratoUpdate, ContratoStatus,
    Projeto, ProjetoUpdate, EtapaProjeto,
    Tarefa, TarefaCreate, TarefaUpdate, TarefaStatus,
    Alerta, Notificacao, TipoNotificacao, OperacaoResponse, Log, NivelRisco,
    User, UserCreate, UserUpdate, UserLogin, UserRole, NotificacaoUsuario, Token,
    ESTEIRA_COMPLETA, MacroEtapa
)
from workflow_engine import WorkflowEngine
from geradores import GeradorTarefas, GeradorNotificacoes, CalculadorCriticidade
from auth import hash_password, verify_password, create_access_token, get_current_user, require_permission, oauth2_scheme
from fastapi.security import OAuth2PasswordRequestForm

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="IDEIABH - Sistema de Gestão Operacional")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize Workflow Engine
workflow_engine = WorkflowEngine(db)
gerador_tarefas = GeradorTarefas(db)
gerador_notificacoes = GeradorNotificacoes(db)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ AUTENTICAÇÃO ============

@api_router.post("/auth/register", response_model=Token)
async def registrar_usuario(user_data: UserCreate):
    """Registra novo usuário (primeiro será admin)"""
    try:
        # Verificar se email já existe
        existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        
        # Verificar se é o primeiro usuário (será admin)
        count = await db.users.count_documents({})
        is_first = count == 0
        
        user = User(
            nome=user_data.nome,
            email=user_data.email,
            senha_hash=hash_password(user_data.senha),
            role=UserRole.ADMIN if is_first else user_data.role,
            permissoes={
                "dashboard": True,
                "contratos_visualizar": True,
                "contratos_criar": is_first,
                "contratos_editar": is_first,
                "contratos_excluir": is_first,
                "contratos_aprovar": is_first,
                "contratos_finalizar": is_first,
                "projetos_visualizar": True,
                "projetos_avancar": is_first,
                "tarefas_visualizar": True,
                "tarefas_criar": is_first,
                "tarefas_editar": is_first,
                "tarefas_concluir": True,
                "tarefas_mover": is_first,
                "admin": is_first
            }
        )
        
        user_dict = user.dict()
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        await db.users.insert_one(user_dict)
        
        # Criar token
        access_token = create_access_token(data={"sub": user.id})
        
        user_response = user_dict.copy()
        del user_response['senha_hash']
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Faz login e retorna token JWT"""
    try:
        user_data = await db.users.find_one({"email": form_data.username}, {"_id": 0})
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos"
            )
        
        if not verify_password(form_data.password, user_data['senha_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos"
            )
        
        if not user_data.get('ativo', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo"
            )
        
        # Criar token
        access_token = create_access_token(data={"sub": user_data['id']})
        
        # Retornar dados do usuário (sem senha)
        user_response = user_data.copy()
        del user_response['senha_hash']
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao fazer login: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/me")
async def get_me(token: str = Depends(oauth2_scheme)):
    """Retorna dados do usuário logado"""
    user = await get_current_user(token, db)
    user_copy = user.copy()
    if 'senha_hash' in user_copy:
        del user_copy['senha_hash']
    return user_copy

# ============ ADMINISTRAÇÃO ============

async def get_current_user_dep(token: str = Depends(oauth2_scheme)):
    """Dependency para obter usuário atual"""
    return await get_current_user(token, db)

@api_router.get("/admin/users")
async def listar_usuarios(current_user: dict = Depends(get_current_user_dep)):
    """Lista todos os usuários (apenas admin)"""
    await require_permission("admin", current_user)
    
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    for user in users:
        if 'senha_hash' in user:
            del user['senha_hash']
    return users

@api_router.post("/admin/users")
async def criar_usuario_admin(
    user_data: UserCreate,
    current_user: dict = Depends(get_current_user_dep)
):
    """Cria novo usuário (apenas admin)"""
    await require_permission("admin", current_user)
    
    try:
        existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        
        user = User(
            nome=user_data.nome,
            email=user_data.email,
            senha_hash=hash_password(user_data.senha),
            role=user_data.role
        )
        
        user_dict = user.dict()
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        await db.users.insert_one(user_dict)
        
        return {"message": "Usuário criado com sucesso", "user_id": user.id}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/admin/users/{user_id}")
async def atualizar_usuario(
    user_id: str,
    update: UserUpdate,
    current_user: dict = Depends(get_current_user_dep)
):
    """Atualiza usuário (apenas admin)"""
    await require_permission("admin", current_user)
    
    try:
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        update_data = {k: v for k, v in update.dict().items() if v is not None}
        
        # Se alterando senha, fazer hash
        if 'senha' in update_data:
            update_data['senha_hash'] = hash_password(update_data['senha'])
            del update_data['senha']
        
        if 'role' in update_data:
            update_data['role'] = update_data['role'].value
        
        await db.users.update_one({"id": user_id}, {"$set": update_data})
        
        return {"message": "Usuário atualizado com sucesso"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao atualizar usuário: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/admin/users/{user_id}")
async def excluir_usuario(
    user_id: str,
    current_user: dict = Depends(get_current_user_dep)
):
    """Exclui usuário (apenas admin)"""
    await require_permission("admin", current_user)
    
    await db.users.delete_one({"id": user_id})
    return {"message": "Usuário excluído com sucesso"}

# ============ NOTIFICAÇÕES ============

@api_router.get("/notificacoes/{user_id}")
async def obter_notificacoes(user_id: str):
    """Obtém notificações do usuário"""
    notificacoes = await db.notificacoes_usuarios.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return notificacoes

@api_router.put("/notificacoes/{notificacao_id}/ler")
async def marcar_notificacao_lida(notificacao_id: str):
    """Marca notificação como lida"""
    await db.notificacoes_usuarios.update_one(
        {"id": notificacao_id},
        {"$set": {"lida": True}}
    )
    return {"message": "Notificação marcada como lida"}

@api_router.put("/notificacoes/{user_id}/ler-todas")
async def marcar_todas_lidas(user_id: str):
    """Marca todas as notificações como lidas"""
    await db.notificacoes_usuarios.update_many(
        {"user_id": user_id, "lida": False},
        {"$set": {"lida": True}}
    )
    return {"message": "Todas as notificações marcadas como lidas"}

# ============ CONTRATOS ============

@api_router.post("/contratos", response_model=OperacaoResponse)
async def criar_contrato(contrato_input: ContratoCreate):
    """
    CRIAR CONTRATO
    - Valida campos obrigatórios
    - Cria contrato
    - Cria projeto vinculado
    - Gera APENAS tarefas da etapa Lançamento (geração progressiva)
    """
    try:
        # Criar contrato
        contrato = Contrato(**contrato_input.dict())
        
        # Criar log
        log = Log(
            acao="criar_contrato",
            usuario="Sistema",
            detalhes={"cliente": contrato.cliente, "valor": contrato.valor}
        )
        contrato.logs.append(log)
        
        # Inserir no banco
        contrato_dict = contrato.dict()
        contrato_dict['status'] = contrato_dict['status'].value
        contrato_dict['data_inicio'] = contrato_dict['data_inicio'].isoformat()
        contrato_dict['data_fim'] = contrato_dict['data_fim'].isoformat()
        contrato_dict['created_at'] = contrato_dict['created_at'].isoformat()
        contrato_dict['logs'] = [l.dict() for l in contrato.logs]
        for log_item in contrato_dict['logs']:
            log_item['timestamp'] = log_item['timestamp'].isoformat()
        
        await db.contratos.insert_one(contrato_dict)
        
        # Criar projeto vinculado
        projeto = Projeto(
            contrato_id=contrato.id,
            data_entrega=contrato.data_fim,
            etapa_atual=EtapaProjeto.LANCAMENTO,
            macro_etapa=MacroEtapa.ATENDIMENTO
        )
        
        projeto_dict = projeto.dict()
        projeto_dict['etapa_atual'] = projeto_dict['etapa_atual'].value
        projeto_dict['macro_etapa'] = projeto_dict['macro_etapa'].value
        projeto_dict['risco'] = projeto_dict['risco'].value
        projeto_dict['data_entrega'] = projeto_dict['data_entrega'].isoformat()
        projeto_dict['created_at'] = projeto_dict['created_at'].isoformat()
        projeto_dict['logs'] = []
        
        await db.projetos.insert_one(projeto_dict)
        
        # Atualizar contrato com projeto_id
        await db.contratos.update_one(
            {"id": contrato.id},
            {"$set": {"projeto_id": projeto.id}}
        )
        
        # GERAR APENAS TAREFAS DA PRIMEIRA ETAPA (Lançamento)
        tarefas_criadas = await gerador_tarefas.gerar_tarefas_etapa(
            projeto.id,
            EtapaProjeto.LANCAMENTO,
            contrato.data_inicio
        )
        
        # Notificar responsáveis
        for tarefa in tarefas_criadas:
            await gerador_notificacoes.notificar_tarefa_atribuida(tarefa)
        
        logger.info(f"Contrato {contrato.id} criado com sucesso - {len(tarefas_criadas)} tarefas geradas")
        
        return OperacaoResponse(
            status="success",
            acao_executada="criar_contrato",
            dados_afetados={
                "contrato_id": contrato.id,
                "projeto_id": projeto.id,
                "tarefas_criadas": len(tarefas_criadas)
            },
            logs=[{
                "acao": "criar_contrato",
                "timestamp": datetime.utcnow().isoformat(),
                "detalhes": f"Contrato criado para {contrato.cliente} com {len(tarefas_criadas)} tarefas iniciais"
            }]
        )
    
    except ValueError as e:
        return OperacaoResponse(
            status="blocked",
            acao_executada="criar_contrato",
            motivo=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao criar contrato: {str(e)}")
        return OperacaoResponse(
            status="error",
            acao_executada="criar_contrato",
            motivo=f"Erro interno: {str(e)}"
        )

@api_router.get("/contratos")
async def listar_contratos():
    """Lista todos os contratos"""
    contratos = await db.contratos.find({}, {"_id": 0}).to_list(1000)
    return contratos

@api_router.get("/contratos/{contrato_id}")
async def obter_contrato(contrato_id: str):
    """Obtém um contrato específico"""
    contrato = await db.contratos.find_one({"id": contrato_id}, {"_id": 0})
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    return contrato

@api_router.put("/contratos/{contrato_id}", response_model=OperacaoResponse)
async def atualizar_contrato(contrato_id: str, update: ContratoUpdate):
    """
    ATUALIZAR CONTRATO
    - Se status = Aprovado: libera geração de tarefas
    - Se datas alteradas: recalcula prazos
    """
    try:
        contrato = await db.contratos.find_one({"id": contrato_id})
        if not contrato:
            return OperacaoResponse(
                status="blocked",
                acao_executada="atualizar_contrato",
                motivo="Contrato não encontrado"
            )
        
        update_data = {k: v for k, v in update.dict().items() if v is not None}
        
        # Converter datas para ISO string
        if 'data_inicio' in update_data:
            update_data['data_inicio'] = update_data['data_inicio'].isoformat()
        if 'data_fim' in update_data:
            update_data['data_fim'] = update_data['data_fim'].isoformat()
        if 'status' in update_data:
            update_data['status'] = update_data['status'].value
        
        emails_disparados = []
        
        # Se status mudou para Aprovado
        if update.status == ContratoStatus.APROVADO and contrato.get('status') != ContratoStatus.APROVADO.value:
            # Gerar tarefas da etapa Criação
            projeto_id = contrato.get('projeto_id')
            if projeto_id:
                tarefas = await workflow_engine.gerar_tarefas_criacao(projeto_id, contrato_id)
                
                # Criar notificações para cada tarefa
                for tarefa in tarefas:
                    await workflow_engine.criar_notificacao(
                        destinatario=tarefa.responsavel,
                        assunto=f"Nova tarefa atribuída: {tarefa.titulo}",
                        corpo=f"Você foi designado para a tarefa: {tarefa.titulo}\nPrazo: {tarefa.prazo}\nProjeto: {contrato.get('cliente')}",
                        tipo="atribuicao"
                    )
                    emails_disparados.append(tarefa.responsavel)
        
        await db.contratos.update_one(
            {"id": contrato_id},
            {"$set": update_data}
        )
        
        logger.info(f"Contrato {contrato_id} atualizado")
        
        return OperacaoResponse(
            status="success",
            acao_executada="atualizar_contrato",
            dados_afetados={"contrato_id": contrato_id},
            emails_disparados=emails_disparados,
            logs=[{
                "acao": "atualizar_contrato",
                "timestamp": datetime.utcnow().isoformat(),
                "detalhes": f"Contrato atualizado: {update_data}"
            }]
        )
    
    except Exception as e:
        logger.error(f"Erro ao atualizar contrato: {str(e)}")
        return OperacaoResponse(
            status="error",
            acao_executada="atualizar_contrato",
            motivo=f"Erro: {str(e)}"
        )

@api_router.put("/contratos/{contrato_id}/aprovar", response_model=OperacaoResponse)
async def aprovar_contrato(contrato_id: str):
    """
    APROVAR CONTRATO
    - Muda status para Em Andamento
    - Avança projeto para etapa de Ativação
    - Gera tarefas da etapa Ativação
    """
    try:
        contrato = await db.contratos.find_one({"id": contrato_id}, {"_id": 0})
        if not contrato:
            return OperacaoResponse(
                status="blocked",
                acao_executada="aprovar_contrato",
                motivo="Contrato não encontrado"
            )
        
        if contrato.get('status') != ContratoStatus.ATIVO.value:
            return OperacaoResponse(
                status="blocked",
                acao_executada="aprovar_contrato",
                motivo=f"Contrato deve estar com status 'Ativo' para ser aprovado. Status atual: {contrato.get('status')}"
            )
        
        # Atualizar status do contrato
        await db.contratos.update_one(
            {"id": contrato_id},
            {"$set": {"status": ContratoStatus.EM_ANDAMENTO.value}}
        )
        
        # Buscar projeto vinculado
        projeto_id = contrato.get('projeto_id')
        if not projeto_id:
            return OperacaoResponse(
                status="error",
                acao_executada="aprovar_contrato",
                motivo="Projeto vinculado não encontrado"
            )
        
        # Avançar projeto para Ativação e gerar tarefas
        projeto = await db.projetos.find_one({"id": projeto_id}, {"_id": 0})
        if projeto:
            # Atualizar projeto para etapa Ativação
            await db.projetos.update_one(
                {"id": projeto_id},
                {"$set": {
                    "etapa_atual": EtapaProjeto.ATIVACAO.value,
                    "macro_etapa": MacroEtapa.ATENDIMENTO.value
                }}
            )
            
            # Gerar tarefas da etapa Ativação
            data_base = datetime.utcnow()
            tarefas_criadas = await gerador_tarefas.gerar_tarefas_etapa(
                projeto_id,
                EtapaProjeto.ATIVACAO,
                data_base
            )
            
            # Notificar responsáveis
            for tarefa in tarefas_criadas:
                await gerador_notificacoes.notificar_tarefa_atribuida(tarefa)
        
        logger.info(f"Contrato {contrato_id} aprovado - {len(tarefas_criadas) if 'tarefas_criadas' in locals() else 0} tarefas geradas")
        
        return OperacaoResponse(
            status="success",
            acao_executada="aprovar_contrato",
            dados_afetados={
                "contrato_id": contrato_id,
                "status_novo": ContratoStatus.EM_ANDAMENTO.value,
                "tarefas_criadas": len(tarefas_criadas) if 'tarefas_criadas' in locals() else 0
            },
            logs=[{
                "acao": "aprovar_contrato",
                "timestamp": datetime.utcnow().isoformat(),
                "detalhes": "Contrato aprovado e projeto avançado para Ativação"
            }]
        )
    
    except Exception as e:
        logger.error(f"Erro ao aprovar contrato: {str(e)}")
        return OperacaoResponse(
            status="error",
            acao_executada="aprovar_contrato",
            motivo=f"Erro: {str(e)}"
        )

@api_router.put("/contratos/{contrato_id}/finalizar", response_model=OperacaoResponse)
async def finalizar_contrato(contrato_id: str):
    """
    FINALIZAR CONTRATO
    - Verifica se projeto está completo
    - Muda status para Finalizado
    - Marca projeto como Encerrado
    """
    try:
        contrato = await db.contratos.find_one({"id": contrato_id}, {"_id": 0})
        if not contrato:
            return OperacaoResponse(
                status="blocked",
                acao_executada="finalizar_contrato",
                motivo="Contrato não encontrado"
            )
        
        # Verificar projeto
        projeto_id = contrato.get('projeto_id')
        if projeto_id:
            projeto = await db.projetos.find_one({"id": projeto_id}, {"_id": 0})
            
            # Verificar se todas as tarefas estão concluídas
            tarefas = await db.tarefas.find({"projeto_id": projeto_id}, {"_id": 0}).to_list(1000)
            tarefas_pendentes = [t for t in tarefas if t.get('status') != TarefaStatus.CONCLUIDO.value]
            
            if tarefas_pendentes:
                return OperacaoResponse(
                    status="blocked",
                    acao_executada="finalizar_contrato",
                    motivo=f"Ainda existem {len(tarefas_pendentes)} tarefa(s) pendente(s)",
                    dados_afetados={"tarefas_pendentes": [t.get('titulo') for t in tarefas_pendentes[:5]]}
                )
            
            # Atualizar projeto para Encerrado
            await db.projetos.update_one(
                {"id": projeto_id},
                {"$set": {
                    "etapa_atual": EtapaProjeto.ENCERRADO.value,
                    "macro_etapa": MacroEtapa.POS_VENDAS.value,
                    "progresso": 100.0
                }}
            )
        
        # Atualizar status do contrato
        await db.contratos.update_one(
            {"id": contrato_id},
            {"$set": {"status": ContratoStatus.FINALIZADO.value}}
        )
        
        logger.info(f"Contrato {contrato_id} finalizado")
        
        return OperacaoResponse(
            status="success",
            acao_executada="finalizar_contrato",
            dados_afetados={
                "contrato_id": contrato_id,
                "status_novo": ContratoStatus.FINALIZADO.value
            },
            logs=[{
                "acao": "finalizar_contrato",
                "timestamp": datetime.utcnow().isoformat(),
                "detalhes": "Contrato finalizado com sucesso"
            }]
        )
    
    except Exception as e:
        logger.error(f"Erro ao finalizar contrato: {str(e)}")
        return OperacaoResponse(
            status="error",
            acao_executada="finalizar_contrato",
            motivo=f"Erro: {str(e)}"
        )

@api_router.delete("/contratos/{contrato_id}", response_model=OperacaoResponse)
async def excluir_contrato(contrato_id: str):
    """
    EXCLUIR CONTRATO
    - Bloqueia se produção iniciada
    - Caso contrário: exclusão em cascata
    """
    try:
        contrato = await db.contratos.find_one({"id": contrato_id})
        if not contrato:
            return OperacaoResponse(
                status="blocked",
                acao_executada="excluir_contrato",
                motivo="Contrato não encontrado"
            )
        
        # Verificar se produção iniciada
        projeto_id = contrato.get('projeto_id')
        if projeto_id:
            projeto = await db.projetos.find_one({"id": projeto_id})
            if projeto:
                etapa_atual = projeto.get('etapa_atual', '')
                macro_etapa = projeto.get('macro_etapa', '')
                
                # Bloquear se estiver em Produção ou além
                if macro_etapa == MacroEtapa.PRODUCAO.value or macro_etapa == MacroEtapa.POS_VENDAS.value:
                    return OperacaoResponse(
                        status="blocked",
                        acao_executada="excluir_contrato",
                        motivo=f"BLOQUEIO ABSOLUTO: Projeto está em {macro_etapa}. Exclusão não permitida após início da produção."
                    )
                
                # Também bloquear se etapa indica produção
                if any(palavra in etapa_atual for palavra in ['Produção', 'Qualidade', 'Entrega', 'Pós-Vendas']):
                    return OperacaoResponse(
                        status="blocked",
                        acao_executada="excluir_contrato",
                        motivo=f"BLOQUEIO ABSOLUTO: Projeto está na etapa '{etapa_atual}'. Exclusão não permitida após início da produção."
                    )
        
        # Exclusão em cascata
        if projeto_id:
            await db.tarefas.delete_many({"projeto_id": projeto_id})
            await db.projetos.delete_one({"id": projeto_id})
        
        await db.contratos.delete_one({"id": contrato_id})
        
        logger.info(f"Contrato {contrato_id} excluído")
        
        return OperacaoResponse(
            status="success",
            acao_executada="excluir_contrato",
            dados_afetados={"contrato_id": contrato_id},
            logs=[{
                "acao": "excluir_contrato",
                "timestamp": datetime.utcnow().isoformat(),
                "detalhes": "Contrato e dados relacionados excluídos"
            }]
        )
    
    except Exception as e:
        logger.error(f"Erro ao excluir contrato: {str(e)}")
        return OperacaoResponse(
            status="error",
            acao_executada="excluir_contrato",
            motivo=f"Erro: {str(e)}"
        )

# ============ PROJETOS ============

@api_router.get("/projetos")
async def listar_projetos():
    """Lista todos os projetos"""
    projetos = await db.projetos.find({}, {"_id": 0}).to_list(1000)
    # Adicionar campos padrão se não existirem
    for projeto in projetos:
        if 'macro_etapa' not in projeto:
            projeto['macro_etapa'] = MacroEtapa.ATENDIMENTO.value
    return projetos

@api_router.get("/projetos/{projeto_id}")
async def obter_projeto(projeto_id: str):
    """Obtém um projeto específico"""
    projeto = await db.projetos.find_one({"id": projeto_id}, {"_id": 0})
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    # Adicionar campos padrão se não existirem
    if 'macro_etapa' not in projeto:
        projeto['macro_etapa'] = MacroEtapa.ATENDIMENTO.value
    return projeto

@api_router.put("/projetos/{projeto_id}", response_model=OperacaoResponse)
async def atualizar_projeto(projeto_id: str, update: ProjetoUpdate):
    """
    ATUALIZAR PROJETO
    - Valida transição de etapa
    - Atualiza progresso automaticamente
    - Reavalia risco
    """
    try:
        projeto_data = await db.projetos.find_one({"id": projeto_id})
        if not projeto_data:
            return OperacaoResponse(
                status="blocked",
                acao_executada="atualizar_projeto",
                motivo="Projeto não encontrado"
            )
        
        projeto = Projeto(**projeto_data)
        
        # Se mudança de etapa
        if update.etapa_atual:
            valido, motivo = workflow_engine.validar_transicao_etapa(projeto, update.etapa_atual)
            if not valido:
                return OperacaoResponse(
                    status="blocked",
                    acao_executada="atualizar_projeto",
                    motivo=motivo
                )
            
            # Atualizar status do contrato se entrando em produção
            if update.etapa_atual == EtapaProjeto.PRODUCAO:
                await db.contratos.update_one(
                    {"id": projeto.contrato_id},
                    {"$set": {"status": ContratoStatus.EM_PRODUCAO.value}}
                )
        
        update_data = {k: v.value if hasattr(v, 'value') else v for k, v in update.dict().items() if v is not None}
        
        # Recalcular progresso
        progresso = await workflow_engine.calcular_progresso_projeto(projeto_id)
        update_data['progresso'] = progresso
        
        # Reavaliar risco
        risco = await workflow_engine.avaliar_risco_projeto(projeto_id)
        update_data['risco'] = risco.value
        
        await db.projetos.update_one(
            {"id": projeto_id},
            {"$set": update_data}
        )
        
        logger.info(f"Projeto {projeto_id} atualizado")
        
        return OperacaoResponse(
            status="success",
            acao_executada="atualizar_projeto",
            dados_afetados={
                "projeto_id": projeto_id,
                "progresso": progresso,
                "risco": risco.value
            },
            logs=[{
                "acao": "atualizar_projeto",
                "timestamp": datetime.utcnow().isoformat(),
                "detalhes": f"Projeto atualizado"
            }]
        )
    
    except Exception as e:
        logger.error(f"Erro ao atualizar projeto: {str(e)}")
        return OperacaoResponse(
            status="error",
            acao_executada="atualizar_projeto",
            motivo=f"Erro: {str(e)}"
        )

@api_router.get("/projetos/esteira/visualizacao")
async def visualizar_esteira():
    """
    VISUALIZAÇÃO DA ESTEIRA
    - Organiza projetos por macro etapa
    - Retorna estrutura para visualização em colunas
    """
    try:
        projetos = await db.projetos.find({}, {"_id": 0}).to_list(1000)
        contratos = await db.contratos.find({}, {"_id": 0}).to_list(1000)
        
        # Mapear contratos por ID
        contratos_map = {c['id']: c for c in contratos}
        
        # Organizar por macro etapa
        esteira = {
            "PRE_PRODUCAO": {
                "titulo": "Pré-Produção",
                "cor": "#3b82f6",
                "projetos": []
            },
            "PRODUCAO": {
                "titulo": "Produção",
                "cor": "#f59e0b",
                "projetos": []
            },
            "POS_PRODUCAO": {
                "titulo": "Pós-Produção",
                "cor": "#10b981",
                "projetos": []
            }
        }
        
        for projeto in projetos:
            # Enriquecer dados do projeto
            contrato = contratos_map.get(projeto.get('contrato_id'), {})
            
            projeto_info = {
                **projeto,
                "cliente": contrato.get('cliente', 'Cliente'),
                "faculdade": contrato.get('faculdade', ''),
                "numero_contrato": contrato.get('numero_contrato', 0),
                "valor": contrato.get('valor', 0)
            }
            
            # Determinar coluna baseado na macro etapa
            macro = projeto.get('macro_etapa', MacroEtapa.ATENDIMENTO.value)
            
            if macro in [MacroEtapa.ATENDIMENTO.value, MacroEtapa.CLIENTE.value, MacroEtapa.PREPARACAO.value, MacroEtapa.CRIACAO.value, MacroEtapa.PRE_PRODUCAO.value]:
                esteira["PRE_PRODUCAO"]["projetos"].append(projeto_info)
            elif macro == MacroEtapa.PRODUCAO.value:
                esteira["PRODUCAO"]["projetos"].append(projeto_info)
            elif macro == MacroEtapa.POS_VENDAS.value:
                esteira["POS_PRODUCAO"]["projetos"].append(projeto_info)
            else:
                # Default para pré-produção
                esteira["PRE_PRODUCAO"]["projetos"].append(projeto_info)
        
        return esteira
    
    except Exception as e:
        logger.error(f"Erro ao visualizar esteira: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/projetos/{projeto_id}/finalizar", response_model=OperacaoResponse)
async def finalizar_projeto(projeto_id: str):
    """
    FINALIZAR PROJETO
    - Valida que todas as tarefas estão concluídas
    - Atualiza contrato para Entregue
    """
    try:
        projeto = await db.projetos.find_one({"id": projeto_id})
        if not projeto:
            return OperacaoResponse(
                status="blocked",
                acao_executada="finalizar_projeto",
                motivo="Projeto não encontrado"
            )
        
        # Verificar se todas as tarefas estão concluídas
        tarefas = await db.tarefas.find({"projeto_id": projeto_id}).to_list(1000)
        tarefas_pendentes = [t for t in tarefas if t.get('status') != TarefaStatus.CONCLUIDO.value]
        
        if tarefas_pendentes:
            return OperacaoResponse(
                status="blocked",
                acao_executada="finalizar_projeto",
                motivo=f"Ainda existem {len(tarefas_pendentes)} tarefa(s) pendente(s)",
                dados_afetados={"tarefas_pendentes": [t.get('titulo') for t in tarefas_pendentes]}
            )
        
        # Atualizar projeto
        await db.projetos.update_one(
            {"id": projeto_id},
            {"$set": {"progresso": 100.0, "risco": NivelRisco.BAIXO.value}}
        )
        
        # Atualizar contrato
        await db.contratos.update_one(
            {"id": projeto.get('contrato_id')},
            {"$set": {"status": ContratoStatus.ENTREGUE.value}}
        )
        
        # Criar notificação de conclusão
        contrato = await db.contratos.find_one({"id": projeto.get('contrato_id')})
        await workflow_engine.criar_notificacao(
            destinatario="gerencia@ideiabh.com",
            assunto=f"Projeto finalizado: {contrato.get('cliente')}",
            corpo=f"O projeto para {contrato.get('cliente')} foi concluído com sucesso!",
            tipo="projeto_entregue"
        )
        
        logger.info(f"Projeto {projeto_id} finalizado")
        
        return OperacaoResponse(
            status="success",
            acao_executada="finalizar_projeto",
            dados_afetados={"projeto_id": projeto_id},
            emails_disparados=["gerencia@ideiabh.com"],
            logs=[{
                "acao": "finalizar_projeto",
                "timestamp": datetime.utcnow().isoformat(),
                "detalhes": "Projeto finalizado com sucesso"
            }]
        )
    
    except Exception as e:
        logger.error(f"Erro ao finalizar projeto: {str(e)}")
        return OperacaoResponse(
            status="error",
            acao_executada="finalizar_projeto",
            motivo=f"Erro: {str(e)}"
        )

@api_router.post("/projetos/{projeto_id}/avancar-macro-etapa", response_model=OperacaoResponse)
async def avancar_macro_etapa(projeto_id: str):
    """
    AVANÇAR MACRO ETAPA DO PROJETO (para mover entre colunas da esteira)
    - Pré-Produção → Produção → Pós-Produção
    - Valida se todas as tarefas da macro etapa atual estão concluídas
    """
    try:
        projeto = await db.projetos.find_one({"id": projeto_id}, {"_id": 0})
        if not projeto:
            return OperacaoResponse(
                status="blocked",
                acao_executada="avancar_macro_etapa",
                motivo="Projeto não encontrado"
            )
        
        macro_atual = projeto.get('macro_etapa', MacroEtapa.ATENDIMENTO.value)
        
        # Definir sequência de macro etapas
        sequencia = [
            MacroEtapa.ATENDIMENTO.value,
            MacroEtapa.CLIENTE.value,
            MacroEtapa.PREPARACAO.value,
            MacroEtapa.CRIACAO.value,
            MacroEtapa.PRE_PRODUCAO.value,
            MacroEtapa.PRODUCAO.value,
            MacroEtapa.POS_VENDAS.value
        ]
        
        # Encontrar próxima macro etapa
        try:
            idx_atual = sequencia.index(macro_atual)
        except ValueError:
            idx_atual = 0
        
        if idx_atual >= len(sequencia) - 1:
            return OperacaoResponse(
                status="blocked",
                acao_executada="avancar_macro_etapa",
                motivo="Projeto já está na última macro etapa"
            )
        
        proxima_macro = sequencia[idx_atual + 1]
        
        # Verificar se todas as tarefas da macro etapa atual estão concluídas
        tarefas_macro = await db.tarefas.find({
            "projeto_id": projeto_id,
            "macro_etapa": macro_atual
        }, {"_id": 0}).to_list(1000)
        
        tarefas_pendentes = [t for t in tarefas_macro if t.get('status') != TarefaStatus.CONCLUIDO.value]
        
        if tarefas_pendentes:
            return OperacaoResponse(
                status="blocked",
                acao_executada="avancar_macro_etapa",
                motivo=f"Ainda existem {len(tarefas_pendentes)} tarefa(s) pendente(s) na macro etapa atual",
                dados_afetados={"tarefas_pendentes": [t.get('titulo') for t in tarefas_pendentes[:5]]}
            )
        
        # Determinar próxima etapa específica baseada na macro etapa
        proxima_etapa = None
        if proxima_macro == MacroEtapa.PRODUCAO.value:
            proxima_etapa = EtapaProjeto.PLANEJAMENTO_PRODUCAO
        elif proxima_macro == MacroEtapa.POS_VENDAS.value:
            proxima_etapa = EtapaProjeto.POS_VENDAS
        elif proxima_macro == MacroEtapa.PRE_PRODUCAO.value:
            proxima_etapa = EtapaProjeto.PLANEJAMENTO_PRODUCAO
        elif proxima_macro == MacroEtapa.CRIACAO.value:
            proxima_etapa = EtapaProjeto.CRIACAO_1_2
        
        # Atualizar projeto
        update_data = {
            "macro_etapa": proxima_macro
        }
        
        if proxima_etapa:
            update_data["etapa_atual"] = proxima_etapa.value
        
        await db.projetos.update_one(
            {"id": projeto_id},
            {"$set": update_data}
        )
        
        # Gerar tarefas da nova etapa se houver etapa específica
        tarefas_criadas = []
        if proxima_etapa:
            data_base = datetime.utcnow()
            tarefas_criadas = await gerador_tarefas.gerar_tarefas_etapa(
                projeto_id,
                proxima_etapa,
                data_base
            )
            
            # Notificar responsáveis
            for tarefa in tarefas_criadas:
                await gerador_notificacoes.notificar_tarefa_atribuida(tarefa)
        
        # Atualizar status do contrato se entrando em produção
        if proxima_macro == MacroEtapa.PRODUCAO.value:
            contrato = await db.contratos.find_one({"projeto_id": projeto_id}, {"_id": 0})
            if contrato:
                await db.contratos.update_one(
                    {"id": contrato['id']},
                    {"$set": {"status": ContratoStatus.EM_ANDAMENTO.value}}
                )
        
        logger.info(f"Projeto {projeto_id} avançou de {macro_atual} para {proxima_macro}")
        
        return OperacaoResponse(
            status="success",
            acao_executada="avancar_macro_etapa",
            dados_afetados={
                "projeto_id": projeto_id,
                "macro_etapa_anterior": macro_atual,
                "macro_etapa_nova": proxima_macro,
                "etapa_atual": proxima_etapa.value if proxima_etapa else None,
                "tarefas_criadas": len(tarefas_criadas)
            },
            logs=[{
                "acao": "avancar_macro_etapa",
                "timestamp": datetime.utcnow().isoformat(),
                "detalhes": f"Avançado de {macro_atual} para {proxima_macro}"
            }]
        )
    
    except Exception as e:
        logger.error(f"Erro ao avançar macro etapa: {str(e)}")
        import traceback
        traceback.print_exc()
        return OperacaoResponse(
            status="error",
            acao_executada="avancar_macro_etapa",
            motivo=f"Erro: {str(e)}"
        )

@api_router.post("/projetos/{projeto_id}/avancar-etapa", response_model=OperacaoResponse)
async def avancar_etapa_projeto(projeto_id: str):
    """
    AVANÇAR ETAPA DO PROJETO
    - Valida que todas as tarefas da etapa atual estão concluídas
    - Avança para próxima etapa
    - GERA TAREFAS DA PRÓXIMA ETAPA (geração progressiva)
    """
    try:
        projeto_data = await db.projetos.find_one({"id": projeto_id})
        if not projeto_data:
            return OperacaoResponse(
                status="blocked",
                acao_executada="avancar_etapa",
                motivo="Projeto não encontrado"
            )
        
        etapa_atual = EtapaProjeto(projeto_data['etapa_atual'])
        
        # Verificar se todas as tarefas da etapa atual estão concluídas
        tarefas_etapa = await db.tarefas.find({
            "projeto_id": projeto_id,
            "etapa": etapa_atual.value
        }).to_list(1000)
        
        tarefas_pendentes = [t for t in tarefas_etapa if t.get('status') != TarefaStatus.CONCLUIDO.value]
        
        if tarefas_pendentes:
            return OperacaoResponse(
                status="blocked",
                acao_executada="avancar_etapa",
                motivo=f"Ainda existem {len(tarefas_pendentes)} tarefa(s) pendente(s) na etapa atual",
                dados_afetados={"tarefas_pendentes": [t.get('titulo') for t in tarefas_pendentes]}
            )
        
        # Determinar próxima etapa
        todas_etapas = list(EtapaProjeto)
        idx_atual = todas_etapas.index(etapa_atual)
        
        if idx_atual >= len(todas_etapas) - 1:
            return OperacaoResponse(
                status="blocked",
                acao_executada="avancar_etapa",
                motivo="Projeto já está na última etapa"
            )
        
        proxima_etapa = todas_etapas[idx_atual + 1]
        
        # Atualizar projeto
        macro = _get_macro_etapa(proxima_etapa)
        await db.projetos.update_one(
            {"id": projeto_id},
            {"$set": {
                "etapa_atual": proxima_etapa.value,
                "macro_etapa": macro.value
            }}
        )
        
        # GERAR TAREFAS DA PRÓXIMA ETAPA
        data_base = datetime.utcnow()
        tarefas_criadas = await gerador_tarefas.gerar_tarefas_etapa(
            projeto_id,
            proxima_etapa,
            data_base
        )
        
        # Notificar responsáveis
        for tarefa in tarefas_criadas:
            await gerador_notificacoes.notificar_tarefa_atribuida(tarefa)
        
        logger.info(f"Projeto {projeto_id} avançou para {proxima_etapa.value} - {len(tarefas_criadas)} novas tarefas")
        
        return OperacaoResponse(
            status="success",
            acao_executada="avancar_etapa",
            dados_afetados={
                "projeto_id": projeto_id,
                "etapa_anterior": etapa_atual.value,
                "etapa_atual": proxima_etapa.value,
                "novas_tarefas": len(tarefas_criadas)
            },
            logs=[{
                "acao": "avancar_etapa",
                "timestamp": datetime.utcnow().isoformat(),
                "detalhes": f"Etapa avançada de {etapa_atual.value} para {proxima_etapa.value}"
            }]
        )
    
    except Exception as e:
        logger.error(f"Erro ao avançar etapa: {str(e)}")
        return OperacaoResponse(
            status="error",
            acao_executada="avancar_etapa",
            motivo=f"Erro: {str(e)}"
        )

def _get_macro_etapa(etapa: EtapaProjeto) -> MacroEtapa:
    """Retorna macro etapa baseado na etapa"""
    mapeamento = {
        EtapaProjeto.LANCAMENTO: MacroEtapa.ATENDIMENTO,
        EtapaProjeto.ATIVACAO: MacroEtapa.ATENDIMENTO,
        EtapaProjeto.REVISAO_TEXTO: MacroEtapa.PREPARACAO,
        EtapaProjeto.CRIACAO_1_2: MacroEtapa.CRIACAO,
        EtapaProjeto.CONFERENCIA: MacroEtapa.CRIACAO,
        EtapaProjeto.AJUSTE_LAYOUT: MacroEtapa.CRIACAO,
        EtapaProjeto.CRIACAO_3_4: MacroEtapa.CRIACAO,
        EtapaProjeto.APROVACAO_FINAL: MacroEtapa.CRIACAO,
        EtapaProjeto.PLANEJAMENTO_PRODUCAO: MacroEtapa.PRE_PRODUCAO,
        EtapaProjeto.PRE_PRODUCAO: MacroEtapa.PRE_PRODUCAO,
        EtapaProjeto.PRODUCAO: MacroEtapa.PRODUCAO,
        EtapaProjeto.QUALIDADE: MacroEtapa.PRODUCAO,
        EtapaProjeto.ENTREGA: MacroEtapa.PRODUCAO,
        EtapaProjeto.POS_VENDAS: MacroEtapa.POS_VENDAS,
    }
    return mapeamento.get(etapa, MacroEtapa.ATENDIMENTO)

# ============ TAREFAS ============

@api_router.post("/tarefas", response_model=OperacaoResponse)
async def criar_tarefa(tarefa_input: TarefaCreate):
    """
    CRIAR TAREFA
    - Valida projeto e etapa
    - Valida responsável e prazo
    """
    try:
        # Verificar se projeto existe
        projeto = await db.projetos.find_one({"id": tarefa_input.projeto_id})
        if not projeto:
            return OperacaoResponse(
                status="blocked",
                acao_executada="criar_tarefa",
                motivo="Projeto não encontrado"
            )
        
        # Criar tarefa
        tarefa = Tarefa(**tarefa_input.dict())
        
        tarefa_dict = tarefa.dict()
        tarefa_dict['prazo'] = tarefa_dict['prazo'].isoformat()
        tarefa_dict['created_at'] = tarefa_dict['created_at'].isoformat()
        
        await db.tarefas.insert_one(tarefa_dict)
        
        # Criar notificação
        await workflow_engine.criar_notificacao(
            destinatario=tarefa.responsavel,
            assunto=f"Nova tarefa atribuída: {tarefa.titulo}",
            corpo=f"Você foi designado para a tarefa: {tarefa.titulo}\nPrazo: {tarefa.prazo}",
            tipo="atribuicao"
        )
        
        logger.info(f"Tarefa {tarefa.id} criada")
        
        return OperacaoResponse(
            status="success",
            acao_executada="criar_tarefa",
            dados_afetados={"tarefa_id": tarefa.id},
            emails_disparados=[tarefa.responsavel],
            logs=[{
                "acao": "criar_tarefa",
                "timestamp": datetime.utcnow().isoformat(),
                "detalhes": f"Tarefa '{tarefa.titulo}' criada"
            }]
        )
    
    except Exception as e:
        logger.error(f"Erro ao criar tarefa: {str(e)}")
        return OperacaoResponse(
            status="error",
            acao_executada="criar_tarefa",
            motivo=f"Erro: {str(e)}"
        )

@api_router.get("/tarefas")
async def listar_tarefas(projeto_id: Optional[str] = None, etapa: Optional[str] = None):
    """Lista tarefas com filtros opcionais"""
    query = {}
    if projeto_id:
        query['projeto_id'] = projeto_id
    if etapa:
        query['etapa'] = etapa
    
    tarefas = await db.tarefas.find(query, {"_id": 0}).to_list(1000)
    # Adicionar campos padrão se não existirem
    for tarefa in tarefas:
        if 'macro_etapa' not in tarefa:
            tarefa['macro_etapa'] = MacroEtapa.ATENDIMENTO.value
        if 'numero' not in tarefa:
            tarefa['numero'] = 0
        if 'atividade' not in tarefa:
            tarefa['atividade'] = tarefa.get('titulo', 'Atividade')
        if 'setor' not in tarefa:
            tarefa['setor'] = 'Geral'
    return tarefas

@api_router.get("/tarefas/{tarefa_id}")
async def obter_tarefa(tarefa_id: str):
    """Obtém uma tarefa específica"""
    tarefa = await db.tarefas.find_one({"id": tarefa_id}, {"_id": 0})
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    # Adicionar campos padrão se não existirem
    if 'macro_etapa' not in tarefa:
        tarefa['macro_etapa'] = MacroEtapa.ATENDIMENTO.value
    if 'numero' not in tarefa:
        tarefa['numero'] = 0
    if 'atividade' not in tarefa:
        tarefa['atividade'] = tarefa.get('titulo', 'Atividade')
    if 'setor' not in tarefa:
        tarefa['setor'] = 'Geral'
    return tarefa

@api_router.put("/tarefas/{tarefa_id}", response_model=OperacaoResponse)
async def atualizar_tarefa(tarefa_id: str, update: TarefaUpdate):
    """
    ATUALIZAR TAREFA
    - Valida dependências se mudando para Em Andamento
    - Atualiza progresso do projeto
    - Eleva risco se tarefa crítica atrasar
    """
    try:
        tarefa_data = await db.tarefas.find_one({"id": tarefa_id})
        if not tarefa_data:
            return OperacaoResponse(
                status="blocked",
                acao_executada="atualizar_tarefa",
                motivo="Tarefa não encontrada"
            )
        
        tarefa = Tarefa(**tarefa_data)
        
        # Validar dependências se iniciando tarefa
        if update.status in [TarefaStatus.EM_ANDAMENTO, TarefaStatus.CONCLUIDO]:
            valido, motivo = workflow_engine.validar_dependencias_tarefa(tarefa)
            if not valido:
                return OperacaoResponse(
                    status="blocked",
                    acao_executada="atualizar_tarefa",
                    motivo=motivo
                )
        
        update_data = {k: v for k, v in update.dict().items() if v is not None}
        
        # Converter enums e datas
        if 'status' in update_data:
            update_data['status'] = update_data['status'].value
        if 'prazo' in update_data:
            update_data['prazo'] = update_data['prazo'].isoformat()
        
        await db.tarefas.update_one(
            {"id": tarefa_id},
            {"$set": update_data}
        )
        
        # Atualizar progresso do projeto
        progresso = await workflow_engine.calcular_progresso_projeto(tarefa.projeto_id)
        risco = await workflow_engine.avaliar_risco_projeto(tarefa.projeto_id)
        
        await db.projetos.update_one(
            {"id": tarefa.projeto_id},
            {"$set": {"progresso": progresso, "risco": risco.value}}
        )
        
        logger.info(f"Tarefa {tarefa_id} atualizada")
        
        return OperacaoResponse(
            status="success",
            acao_executada="atualizar_tarefa",
            dados_afetados={
                "tarefa_id": tarefa_id,
                "projeto_progresso": progresso,
                "projeto_risco": risco.value
            },
            logs=[{
                "acao": "atualizar_tarefa",
                "timestamp": datetime.utcnow().isoformat(),
                "detalhes": f"Tarefa atualizada"
            }]
        )
    
    except Exception as e:
        logger.error(f"Erro ao atualizar tarefa: {str(e)}")
        return OperacaoResponse(
            status="error",
            acao_executada="atualizar_tarefa",
            motivo=f"Erro: {str(e)}"
        )

@api_router.put("/tarefas/{tarefa_id}/mover", response_model=OperacaoResponse)
async def mover_tarefa(tarefa_id: str, nova_etapa: str):
    """
    MOVER TAREFA (Drag and Drop)
    - Move tarefa para nova etapa/coluna
    - Atualiza macro etapa automaticamente
    - Valida se movimento é permitido
    """
    try:
        tarefa = await db.tarefas.find_one({"id": tarefa_id}, {"_id": 0})
        if not tarefa:
            return OperacaoResponse(
                status="blocked",
                acao_executada="mover_tarefa",
                motivo="Tarefa não encontrada"
            )
        
        etapa_atual = tarefa.get('etapa')
        
        # Converter string para EtapaProjeto
        try:
            nova_etapa_enum = EtapaProjeto(nova_etapa)
        except ValueError:
            return OperacaoResponse(
                status="blocked",
                acao_executada="mover_tarefa",
                motivo=f"Etapa inválida: {nova_etapa}"
            )
        
        # Determinar nova macro etapa
        nova_macro = _get_macro_etapa(nova_etapa_enum)
        
        # Atualizar tarefa
        await db.tarefas.update_one(
            {"id": tarefa_id},
            {"$set": {
                "etapa": nova_etapa_enum.value,
                "macro_etapa": nova_macro.value,
                "status": TarefaStatus.EM_ANDAMENTO.value if nova_etapa != etapa_atual else tarefa.get('status')
            }}
        )
        
        # Recalcular progresso do projeto
        projeto_id = tarefa.get('projeto_id')
        progresso = await workflow_engine.calcular_progresso_projeto(projeto_id)
        await db.projetos.update_one(
            {"id": projeto_id},
            {"$set": {"progresso": progresso}}
        )
        
        logger.info(f"Tarefa {tarefa_id} movida de {etapa_atual} para {nova_etapa_enum.value}")
        
        return OperacaoResponse(
            status="success",
            acao_executada="mover_tarefa",
            dados_afetados={
                "tarefa_id": tarefa_id,
                "etapa_anterior": etapa_atual,
                "etapa_nova": nova_etapa_enum.value
            }
        )
    
    except Exception as e:
        logger.error(f"Erro ao mover tarefa: {str(e)}")
        return OperacaoResponse(
            status="error",
            acao_executada="mover_tarefa",
            motivo=f"Erro: {str(e)}"
        )


@api_router.delete("/tarefas/{tarefa_id}", response_model=OperacaoResponse)
async def excluir_tarefa(tarefa_id: str):
    """
    EXCLUIR TAREFA
    - Bloqueia se tarefa for obrigatória do fluxo
    """
    try:
        tarefa = await db.tarefas.find_one({"id": tarefa_id})
        if not tarefa:
            return OperacaoResponse(
                status="blocked",
                acao_executada="excluir_tarefa",
                motivo="Tarefa não encontrada"
            )
        
        # Verificar se é tarefa obrigatória (crítica)
        if tarefa.get('critica', False):
            return OperacaoResponse(
                status="blocked",
                acao_executada="excluir_tarefa",
                motivo="Tarefa crítica não pode ser excluída. É obrigatória do fluxo."
            )
        
        await db.tarefas.delete_one({"id": tarefa_id})
        
        logger.info(f"Tarefa {tarefa_id} excluída")
        
        return OperacaoResponse(
            status="success",
            acao_executada="excluir_tarefa",
            dados_afetados={"tarefa_id": tarefa_id},
            logs=[{
                "acao": "excluir_tarefa",
                "timestamp": datetime.utcnow().isoformat(),
                "detalhes": "Tarefa excluída"
            }]
        )
    
    except Exception as e:
        logger.error(f"Erro ao excluir tarefa: {str(e)}")
        return OperacaoResponse(
            status="error",
            acao_executada="excluir_tarefa",
            motivo=f"Erro: {str(e)}"
        )

# ============ ALERTAS E MONITORAMENTO ============

@api_router.get("/tarefas/kanban/{projeto_id}")
async def visualizar_kanban(projeto_id: str):
    """
    VISUALIZAÇÃO KANBAN (Estilo Trello)
    - Organiza tarefas por etapa em colunas
    - Permite drag and drop entre colunas
    """
    try:
        tarefas = await db.tarefas.find({"projeto_id": projeto_id}, {"_id": 0}).to_list(1000)
        
        # Definir colunas do Kanban (etapas principais)
        kanban = {
            "LANCAMENTO": {
                "titulo": "Lançamento",
                "cor": "#6366f1",
                "tarefas": []
            },
            "ATIVACAO": {
                "titulo": "Ativação",
                "cor": "#8b5cf6",
                "tarefas": []
            },
            "REVISAO": {
                "titulo": "Revisão/Preparação",
                "cor": "#ec4899",
                "tarefas": []
            },
            "CRIACAO_1_2": {
                "titulo": "Criação (1ª/2ª)",
                "cor": "#f59e0b",
                "tarefas": []
            },
            "CRIACAO_3_4": {
                "titulo": "Criação (3ª/4ª)",
                "cor": "#f97316",
                "tarefas": []
            },
            "APROVACAO": {
                "titulo": "Aprovação Final",
                "cor": "#10b981",
                "tarefas": []
            },
            "PLANEJAMENTO": {
                "titulo": "Planejamento",
                "cor": "#3b82f6",
                "tarefas": []
            },
            "PRE_PRODUCAO": {
                "titulo": "Pré-Produção",
                "cor": "#06b6d4",
                "tarefas": []
            },
            "PRODUCAO": {
                "titulo": "Produção",
                "cor": "#14b8a6",
                "tarefas": []
            },
            "CONCLUIDO": {
                "titulo": "Concluído",
                "cor": "#22c55e",
                "tarefas": []
            }
        }
        
        for tarefa in tarefas:
            # Adicionar campos padrão
            if 'macro_etapa' not in tarefa:
                tarefa['macro_etapa'] = MacroEtapa.ATENDIMENTO.value
            if 'numero' not in tarefa:
                tarefa['numero'] = 0
            if 'atividade' not in tarefa:
                tarefa['atividade'] = tarefa.get('titulo', 'Atividade')
            if 'setor' not in tarefa:
                tarefa['setor'] = 'Geral'
            
            etapa = tarefa.get('etapa', '')
            
            # Mapear para colunas do Kanban
            if EtapaProjeto.LANCAMENTO.value in etapa:
                kanban["LANCAMENTO"]["tarefas"].append(tarefa)
            elif EtapaProjeto.ATIVACAO.value in etapa:
                kanban["ATIVACAO"]["tarefas"].append(tarefa)
            elif EtapaProjeto.REVISAO_TEXTO.value in etapa:
                kanban["REVISAO"]["tarefas"].append(tarefa)
            elif EtapaProjeto.CRIACAO_1_2.value in etapa or EtapaProjeto.CONFERENCIA.value in etapa or EtapaProjeto.AJUSTE_LAYOUT.value in etapa:
                kanban["CRIACAO_1_2"]["tarefas"].append(tarefa)
            elif EtapaProjeto.CRIACAO_3_4.value in etapa:
                kanban["CRIACAO_3_4"]["tarefas"].append(tarefa)
            elif EtapaProjeto.APROVACAO_FINAL.value in etapa:
                kanban["APROVACAO"]["tarefas"].append(tarefa)
            elif EtapaProjeto.PLANEJAMENTO_PRODUCAO.value in etapa:
                kanban["PLANEJAMENTO"]["tarefas"].append(tarefa)
            elif EtapaProjeto.PRE_PRODUCAO.value in etapa:
                kanban["PRE_PRODUCAO"]["tarefas"].append(tarefa)
            elif etapa in [EtapaProjeto.PRODUCAO.value, EtapaProjeto.QUALIDADE.value, EtapaProjeto.ENTREGA.value]:
                if tarefa.get('status') == TarefaStatus.CONCLUIDO.value:
                    kanban["CONCLUIDO"]["tarefas"].append(tarefa)
                else:
                    kanban["PRODUCAO"]["tarefas"].append(tarefa)
            else:
                # Tarefas concluídas vão para a coluna final
                if tarefa.get('status') == TarefaStatus.CONCLUIDO.value:
                    kanban["CONCLUIDO"]["tarefas"].append(tarefa)
                else:
                    kanban["LANCAMENTO"]["tarefas"].append(tarefa)
        
        return kanban
    
    except Exception as e:
        logger.error(f"Erro ao visualizar kanban: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/alertas/{projeto_id}", response_model=List[Alerta])
async def obter_alertas(projeto_id: str):
    """Detecta e retorna alertas do projeto"""
    alertas = await workflow_engine.detectar_alertas(projeto_id)
    return alertas

@api_router.get("/dashboard")
async def obter_dashboard():
    """
    DASHBOARD GERENCIAL
    - KPIs em tempo real
    - Projetos em risco
    - Tarefas atrasadas
    - Gargalos
    """
    try:
        # Total de projetos
        total_projetos = await db.projetos.count_documents({})
        
        # Projetos por status
        contratos = await db.contratos.find({}, {"_id": 0}).to_list(1000)
        por_status = {}
        for contrato in contratos:
            status = contrato.get('status', 'Desconhecido')
            por_status[status] = por_status.get(status, 0) + 1
        
        # Projetos em risco
        projetos_risco_alto = await db.projetos.count_documents({"risco": NivelRisco.ALTO.value})
        projetos_risco_medio = await db.projetos.count_documents({"risco": NivelRisco.MEDIO.value})
        
        # Tarefas atrasadas
        tarefas = await db.tarefas.find({}, {"_id": 0}).to_list(1000)
        tarefas_atrasadas = []
        agora = datetime.utcnow()
        
        for tarefa in tarefas:
            if tarefa.get('status') != TarefaStatus.CONCLUIDO.value:
                prazo = tarefa.get('prazo')
                if isinstance(prazo, str):
                    # Remove timezone info se houver
                    prazo = datetime.fromisoformat(prazo.replace('Z', '+00:00').replace('+00:00', ''))
                if isinstance(prazo, datetime):
                    # Garantir que ambos são naive ou ambos aware
                    if prazo.tzinfo is not None:
                        prazo = prazo.replace(tzinfo=None)
                    if prazo < agora:
                        tarefas_atrasadas.append({
                            "id": tarefa.get('id'),
                            "titulo": tarefa.get('titulo'),
                            "responsavel": tarefa.get('responsavel'),
                            "dias_atraso": (agora - prazo).days
                        })
        
        # Tempo médio por etapa (simplificado)
        # TODO: Implementar cálculo real baseado em logs
        
        # Gargalos por responsável
        responsaveis = {}
        for tarefa in tarefas:
            if tarefa.get('status') != TarefaStatus.CONCLUIDO.value:
                resp = tarefa.get('responsavel')
                responsaveis[resp] = responsaveis.get(resp, 0) + 1
        
        # Projetos no prazo
        projetos = await db.projetos.find({}, {"_id": 0}).to_list(1000)
        projetos_no_prazo = 0
        for projeto in projetos:
            if projeto.get('risco') == NivelRisco.BAIXO.value:
                projetos_no_prazo += 1
        
        percentual_no_prazo = round((projetos_no_prazo / total_projetos * 100) if total_projetos > 0 else 0, 2)
        
        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "kpis": {
                "total_projetos": total_projetos,
                "percentual_no_prazo": percentual_no_prazo,
                "projetos_risco_alto": projetos_risco_alto,
                "projetos_risco_medio": projetos_risco_medio,
                "tarefas_atrasadas_total": len(tarefas_atrasadas)
            },
            "projetos_por_status": por_status,
            "tarefas_atrasadas": tarefas_atrasadas[:10],  # Top 10
            "gargalos_responsaveis": sorted(responsaveis.items(), key=lambda x: x[1], reverse=True)[:5]
        }
        
        return dashboard
    
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/")
async def root():
    """Health check"""
    return {
        "sistema": "IDEIABH",
        "descricao": "Motor Inteligente de Gestão Operacional",
        "status": "operacional",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============ NOTIFICAÇÕES ============

@api_router.get("/notificacoes")
async def listar_notificacoes(current_user: dict = Depends(get_current_user_dep)):
    """Lista todas as notificações do usuário logado"""
    try:
        notificacoes = await db.notificacoes.find(
            {"usuario_id": current_user['id']},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return notificacoes
    except Exception as e:
        logger.error(f"Erro ao listar notificações: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/notificacoes/nao-lidas")
async def contar_nao_lidas(current_user: dict = Depends(get_current_user_dep)):
    """Conta notificações não lidas do usuário"""
    try:
        count = await db.notificacoes.count_documents({
            "usuario_id": current_user['id'],
            "lida": False
        })
        return {"count": count}
    except Exception as e:
        logger.error(f"Erro ao contar notificações: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/notificacoes/{notificacao_id}/ler")
async def marcar_como_lida(notificacao_id: str, current_user: dict = Depends(get_current_user_dep)):
    """Marca uma notificação como lida"""
    try:
        result = await db.notificacoes.update_one(
            {"id": notificacao_id, "usuario_id": current_user['id']},
            {"$set": {"lida": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Notificação não encontrada")
        
        return {"message": "Notificação marcada como lida"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao marcar notificação como lida: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/notificacoes/ler-todas")
async def marcar_todas_como_lidas(current_user: dict = Depends(get_current_user_dep)):
    """Marca todas as notificações do usuário como lidas"""
    try:
        await db.notificacoes.update_many(
            {"usuario_id": current_user['id'], "lida": False},
            {"$set": {"lida": True}}
        )
        return {"message": "Todas as notificações marcadas como lidas"}
    except Exception as e:
        logger.error(f"Erro ao marcar todas como lidas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ DASHBOARD E ESTATÍSTICAS ============

@api_router.get("/dashboard/tarefas-atrasadas")
async def tarefas_atrasadas(current_user: dict = Depends(get_current_user_dep)):
    """Retorna estatísticas de tarefas atrasadas"""
    try:
        agora = datetime.utcnow()
        
        # Buscar tarefas atrasadas
        tarefas = await db.tarefas.find({
            "status": {"$ne": "Concluído"},
            "prazo": {"$lt": agora.isoformat()}
        }, {"_id": 0}).to_list(1000)
        
        # Agrupar por responsável
        por_responsavel = {}
        for tarefa in tarefas:
            resp = tarefa.get('responsavel', 'Não atribuído')
            if resp not in por_responsavel:
                por_responsavel[resp] = []
            por_responsavel[resp].append(tarefa)
        
        # Calcular dias de atraso
        for tarefa in tarefas:
            prazo = datetime.fromisoformat(tarefa['prazo'].replace('Z', ''))
            dias_atraso = (agora - prazo).days
            tarefa['dias_atraso'] = dias_atraso
        
        return {
            "total": len(tarefas),
            "por_responsavel": {k: len(v) for k, v in por_responsavel.items()},
            "tarefas": tarefas
        }
    except Exception as e:
        logger.error(f"Erro ao buscar tarefas atrasadas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/dashboard/proximas-vencer")
async def tarefas_proximas_vencer(current_user: dict = Depends(get_current_user_dep)):
    """Retorna tarefas que vencem em 1 dia"""
    try:
        agora = datetime.utcnow()
        amanha = agora + timedelta(days=1)
        
        tarefas = await db.tarefas.find({
            "status": {"$ne": "Concluído"},
            "prazo": {
                "$gte": agora.isoformat(),
                "$lte": amanha.isoformat()
            }
        }, {"_id": 0}).to_list(1000)
        
        return {"total": len(tarefas), "tarefas": tarefas}
    except Exception as e:
        logger.error(f"Erro ao buscar tarefas próximas ao vencimento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
