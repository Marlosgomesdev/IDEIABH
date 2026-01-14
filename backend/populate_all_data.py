"""
Script para popular o banco de dados com contratos, projetos e tarefas
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import random
import uuid
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Dados fictícios
CLIENTES = [
    "Ana Paula Santos", "Bruno Henrique Lima", "Carlos Eduardo Silva", "Daniela Fernandes Costa",
    "Eduardo Santos Oliveira", "Fernanda Silva Lima", "Gabriel Costa Santos", "Helena Oliveira Silva",
    "Igor Fernandes Costa", "Juliana Santos Lima", "Karina Silva Oliveira", "Leonardo Costa Santos",
    "Mariana Fernandes Silva", "Nicolas Santos Costa", "Olivia Lima Silva", "Pedro Henrique Santos",
    "Queila Costa Lima", "Rafael Silva Santos", "Sara Fernandes Costa", "Thiago Oliveira Lima",
    "Ursula Santos Silva", "Vitor Costa Oliveira", "Wesley Fernandes Lima", "Ximena Silva Santos",
    "Yuri Costa Lima", "Zilda Oliveira Santos", "André Silva Costa", "Beatriz Lima Santos",
    "Caio Fernandes Silva", "Diana Santos Costa"
]

FACULDADES = [
    "Faculdade de Medicina UFMG", "Faculdade de Direito PUC Minas", "Faculdade de Engenharia UEMG",
    "Faculdade de Administração Newton Paiva", "Faculdade de Arquitetura Una", "Faculdade de Computação CEFET-MG",
    "Faculdade de Odontologia UFMG", "Faculdade de Veterinária PUC Minas", "Faculdade de Psicologia Fumec",
    "Faculdade de Nutrição UNA", "Faculdade de Enfermagem UFMG", "Faculdade de Farmácia UEMG",
    "Faculdade de Fisioterapia Newton Paiva", "Faculdade de Design Belas Artes", "Faculdade de Jornalismo PUC Minas",
    "Faculdade de Economia UFMG", "Faculdade de Ciências Contábeis Una", "Faculdade de Marketing Newton Paiva",
    "Faculdade de Engenharia Civil CEFET-MG", "Faculdade de Letras UFMG"
]

SEMESTRES = ["2024/2", "2025/1", "2025/2", "2026/1"]

STATUS_CONTRATOS = ["Ativo", "Em Andamento", "Finalizado"]

ETAPAS = [
    "1 - Lançamento do Contrato",
    "2 - Ativação do Projeto",
    "3 - Revisão de Texto / Preparação das Fotos",
    "4 - Criação (1ª e 2ª AP)",
    "5 - Conferência do Layout",
    "5.1 - Ajuste de Layout",
    "6 - Criação (3ª e 4ª AP)",
    "7 - Aprovação Final (Criação)",
    "8 - Planejamento de Produção",
    "9 - Pré-Produção",
    "10 - Produção",
    "11 - Controle de Qualidade",
    "12 - Entrega",
    "13 - Pós-Vendas",
    "14 - Contrato Encerrado"
]

MACRO_ETAPAS = {
    "1 - Lançamento do Contrato": "Atendimento",
    "2 - Ativação do Projeto": "Atendimento",
    "3 - Revisão de Texto / Preparação das Fotos": "Preparação",
    "4 - Criação (1ª e 2ª AP)": "Criação",
    "5 - Conferência do Layout": "Criação",
    "5.1 - Ajuste de Layout": "Criação",
    "6 - Criação (3ª e 4ª AP)": "Criação",
    "7 - Aprovação Final (Criação)": "Criação",
    "8 - Planejamento de Produção": "Pré-Produção",
    "9 - Pré-Produção": "Pré-Produção",
    "10 - Produção": "Produção",
    "11 - Controle de Qualidade": "Produção",
    "12 - Entrega": "Pós-Vendas",
    "13 - Pós-Vendas": "Pós-Vendas",
    "14 - Contrato Encerrado": "Pós-Vendas"
}

RESPONSAVEIS = [
    "Keyla Nascimento", "Marcos Letro", "Ana Paula Designer", 
    "Bruno Criativo", "Carolina Atendimento", "Rafael Produção",
    "Diana Revisão", "Eduardo Qualidade", "Fernanda Pós-Vendas"
]

ATIVIDADES = {
    "1 - Lançamento do Contrato": "Lançamento do Contrato",
    "2 - Ativação do Projeto": "Apresentação do Projeto",
    "3 - Revisão de Texto / Preparação das Fotos": "Revisão de Texto",
    "4 - Criação (1ª e 2ª AP)": "Criação do Layout",
    "5 - Conferência do Layout": "Conferência do Layout",
    "5.1 - Ajuste de Layout": "Ajuste de Layout",
    "6 - Criação (3ª e 4ª AP)": "Criação 3ª Apresentação",
    "7 - Aprovação Final (Criação)": "Aprovação Final",
    "8 - Planejamento de Produção": "Planejamento de Produção",
    "9 - Pré-Produção": "Pré-Produção",
    "10 - Produção": "Produção",
    "11 - Controle de Qualidade": "Controle de Qualidade",
    "12 - Entrega": "Entrega ao Cliente",
    "13 - Pós-Vendas": "Acompanhamento Pós-Vendas"
}

FEEDBACKS_EM_ANDAMENTO = [
    "Aguardando aprovação do cliente para dar continuidade",
    "Em desenvolvimento, dentro do prazo estabelecido",
    "Necessário validação de algumas informações com o cliente",
    "Aguardando retorno do setor de criação",
    "Em processo de revisão final antes de enviar",
    "Trabalhando em ajustes solicitados pelo cliente",
    "Conferindo detalhes técnicos antes de prosseguir",
    "Aguardando feedback do responsável para finalizar",
    "Em andamento, respeitando o cronograma definido",
    "Dependendo da conclusão de tarefa anterior"
]

FEEDBACKS_CONCLUIDAS = [
    "Tarefa concluída com sucesso e aprovada pelo cliente",
    "Finalizado dentro do prazo estipulado",
    "Concluído após ajustes solicitados, cliente satisfeito",
    "Entrega realizada conforme especificações técnicas",
    "Aprovado sem necessidade de alterações",
    "Concluído e encaminhado para próxima etapa",
    "Finalizado com excelência, cliente elogiou o trabalho",
    "Tarefa concluída antes do prazo previsto",
    "Entregue e aprovado pelo responsável",
    "Concluído após validação de qualidade"
]

FEEDBACKS_ATRASADAS = [
    "Atraso devido a problemas técnicos no sistema de impressão",
    "Cliente demorou para aprovar a versão anterior",
    "Necessário refazer devido a erro de especificação inicial",
    "Atraso causado por falta de materiais necessários",
    "Responsável estava com sobrecarga de trabalho",
    "Problemas de comunicação com fornecedor externo",
    "Cliente solicitou alterações significativas de última hora",
    "Atraso devido a feriado não previsto no cronograma",
    "Necessário aprovação de múltiplos stakeholders",
    "Problemas técnicos com arquivo enviado pelo cliente",
    "Revisor de texto estava de férias, não foi coberto",
    "Equipamento quebrou durante a produção",
    "Cliente não enviou material necessário no prazo",
    "Demanda urgente de outro projeto atrasou esta tarefa",
    "Erro na conferência, necessário refazer layout completo"
]

async def limpar_dados():
    """Limpa dados antigos do banco"""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🗑️  Limpando dados antigos...")
    await db.contratos.delete_many({})
    await db.projetos.delete_many({})
    await db.tarefas.delete_many({})
    print("✅ Dados limpos!")
    
    client.close()

async def criar_dados():
    """Cria todos os dados de uma vez"""
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🚀 Iniciando população do banco de dados...")
    
    contratos_ids = []
    projetos_ids = []
    
    # Criar 20 contratos
    print("\n📋 Criando 20 contratos...")
    for i in range(20):
        cliente = random.choice(CLIENTES)
        faculdade = random.choice(FACULDADES)
        semestre = random.choice(SEMESTRES)
        
        dias_inicio = random.randint(10, 90)
        duracao = random.randint(60, 150)
        data_inicio = datetime.utcnow() - timedelta(days=dias_inicio)
        data_fim = data_inicio + timedelta(days=duracao)
        
        valor = round(random.uniform(3000, 20000), 2)
        status = random.choice(STATUS_CONTRATOS)
        
        contrato_id = str(uuid.uuid4())
        
        contrato = {
            "id": contrato_id,
            "numero_contrato": 2000 + i,
            "cliente": cliente,
            "faculdade": faculdade,
            "semestre": semestre,
            "valor": valor,
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat(),
            "status": status,
            "logs": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        await db.contratos.insert_one(contrato)
        contratos_ids.append((contrato_id, data_fim, cliente, faculdade))
        print(f"  ✅ Contrato #{2000 + i}: {cliente}")
    
    # Criar 35 projetos
    print("\n🎯 Criando 35 projetos...")
    for i in range(35):
        # Escolher um contrato aleatório (alguns contratos terão múltiplos projetos)
        contrato_id, data_entrega, cliente, faculdade = random.choice(contratos_ids)
        
        # Escolher etapa aleatória (mais comum nas etapas intermediárias)
        if i < 5:  # 5 no início
            etapa = random.choice(ETAPAS[:3])
        elif i < 30:  # 25 no meio
            etapa = random.choice(ETAPAS[3:12])
        else:  # 5 no final
            etapa = random.choice(ETAPAS[12:])
        
        macro_etapa = MACRO_ETAPAS[etapa]
        
        # Calcular progresso baseado na etapa
        etapa_num = ETAPAS.index(etapa)
        progresso = (etapa_num / len(ETAPAS)) * 100 + random.uniform(-10, 10)
        progresso = max(0, min(100, progresso))
        
        # Determinar risco
        dias_restantes = (data_entrega - datetime.utcnow()).days
        if dias_restantes < 10:
            risco = "Alto"
        elif dias_restantes < 30:
            risco = "Médio"
        else:
            risco = "Baixo"
        
        projeto_id = str(uuid.uuid4())
        
        projeto = {
            "id": projeto_id,
            "contrato_id": contrato_id,
            "etapa_atual": etapa,
            "macro_etapa": macro_etapa,
            "progresso": round(progresso, 2),
            "risco": risco,
            "data_entrega": data_entrega.isoformat(),
            "responsavel_atendimento": "Keyla Nascimento",
            "responsavel_designer": "Marcos Letro",
            "logs": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        await db.projetos.insert_one(projeto)
        projetos_ids.append((projeto_id, etapa, data_entrega))
        print(f"  ✅ Projeto {i+1}/35: {etapa} - {risco}")
    
    # Criar 60 tarefas (20 em andamento, 10 concluídas, 30 atrasadas)
    print("\n📝 Criando 60 tarefas...")
    
    tarefas_criadas = 0
    
    # 20 tarefas em andamento
    print("  📌 Criando 20 tarefas EM ANDAMENTO...")
    for i in range(20):
        projeto_id, etapa, data_entrega = random.choice(projetos_ids)
        
        prazo = datetime.utcnow() + timedelta(days=random.randint(3, 15))
        
        tarefa_id = str(uuid.uuid4())
        tarefa = {
            "id": tarefa_id,
            "projeto_id": projeto_id,
            "etapa": etapa,
            "macro_etapa": MACRO_ETAPAS[etapa],
            "numero": ETAPAS.index(etapa) + 1,
            "atividade": ATIVIDADES[etapa],
            "setor": MACRO_ETAPAS[etapa],
            "titulo": ATIVIDADES[etapa],
            "descricao": f"Executar {ATIVIDADES[etapa]} para o projeto",
            "responsavel": random.choice(RESPONSAVEIS),
            "prazo": prazo.isoformat(),
            "data_conclusao": None,
            "status": "Em Andamento",
            "observacao": random.choice(FEEDBACKS_EM_ANDAMENTO),
            "dependencias": [],
            "critica": random.choice([True, False]),
            "logs": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        await db.tarefas.insert_one(tarefa)
        tarefas_criadas += 1
        print(f"    ✅ Tarefa {tarefas_criadas}: {tarefa['titulo']} - EM ANDAMENTO")
    
    # 10 tarefas concluídas
    print("  ✅ Criando 10 tarefas CONCLUÍDAS...")
    for i in range(10):
        projeto_id, etapa, data_entrega = random.choice(projetos_ids)
        
        prazo = datetime.utcnow() - timedelta(days=random.randint(5, 20))
        data_conclusao = prazo + timedelta(days=random.randint(0, 3))
        
        tarefa_id = str(uuid.uuid4())
        tarefa = {
            "id": tarefa_id,
            "projeto_id": projeto_id,
            "etapa": etapa,
            "macro_etapa": MACRO_ETAPAS[etapa],
            "numero": ETAPAS.index(etapa) + 1,
            "atividade": ATIVIDADES[etapa],
            "setor": MACRO_ETAPAS[etapa],
            "titulo": ATIVIDADES[etapa],
            "descricao": f"Executar {ATIVIDADES[etapa]} para o projeto",
            "responsavel": random.choice(RESPONSAVEIS),
            "prazo": prazo.isoformat(),
            "data_conclusao": data_conclusao.isoformat(),
            "status": "Concluído",
            "observacao": random.choice(FEEDBACKS_CONCLUIDAS),
            "dependencias": [],
            "critica": random.choice([True, False]),
            "logs": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        await db.tarefas.insert_one(tarefa)
        tarefas_criadas += 1
        print(f"    ✅ Tarefa {tarefas_criadas}: {tarefa['titulo']} - CONCLUÍDA")
    
    # 30 tarefas atrasadas
    print("  🔴 Criando 30 tarefas ATRASADAS...")
    for i in range(30):
        projeto_id, etapa, data_entrega = random.choice(projetos_ids)
        
        # Prazo no passado (atrasada)
        prazo = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        
        tarefa_id = str(uuid.uuid4())
        tarefa = {
            "id": tarefa_id,
            "projeto_id": projeto_id,
            "etapa": etapa,
            "macro_etapa": MACRO_ETAPAS[etapa],
            "numero": ETAPAS.index(etapa) + 1,
            "atividade": ATIVIDADES[etapa],
            "setor": MACRO_ETAPAS[etapa],
            "titulo": ATIVIDADES[etapa],
            "descricao": f"Executar {ATIVIDADES[etapa]} para o projeto",
            "responsavel": random.choice(RESPONSAVEIS),
            "prazo": prazo.isoformat(),
            "data_conclusao": None,
            "status": "Atrasado",
            "observacao": random.choice(FEEDBACKS_ATRASADAS),
            "dependencias": [],
            "critica": True,  # Tarefas atrasadas são sempre críticas
            "logs": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        await db.tarefas.insert_one(tarefa)
        tarefas_criadas += 1
        print(f"    🔴 Tarefa {tarefas_criadas}: {tarefa['titulo']} - ATRASADA")
    
    # Estatísticas finais
    total_contratos = await db.contratos.count_documents({})
    total_projetos = await db.projetos.count_documents({})
    total_tarefas = await db.tarefas.count_documents({})
    tarefas_andamento = await db.tarefas.count_documents({"status": "Em Andamento"})
    tarefas_concluidas = await db.tarefas.count_documents({"status": "Concluído"})
    tarefas_atrasadas = await db.tarefas.count_documents({"status": "Atrasado"})
    
    print(f"\n🎉 População concluída com sucesso!")
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"  📋 Contratos: {total_contratos}")
    print(f"  🎯 Projetos: {total_projetos}")
    print(f"  📝 Tarefas Total: {total_tarefas}")
    print(f"    📌 Em Andamento: {tarefas_andamento}")
    print(f"    ✅ Concluídas: {tarefas_concluidas}")
    print(f"    🔴 Atrasadas: {tarefas_atrasadas}")
    print(f"\n✨ Todas as tarefas possuem feedback/observação!")
    
    client.close()

async def main():
    await limpar_dados()
    await criar_dados()

if __name__ == "__main__":
    asyncio.run(main())
