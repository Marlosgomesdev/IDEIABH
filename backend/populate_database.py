"""
Script para popular o banco de dados com clientes e contratos fictícios
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
    "Maria Santos Silva",
    "João Pedro Oliveira",
    "Ana Carolina Costa",
    "Carlos Eduardo Souza",
    "Juliana Fernandes",
    "Ricardo Almeida Lima",
    "Patricia Rodrigues",
    "Fernando Henrique Santos",
    "Gabriela Martins",
    "Lucas Gabriel Pereira",
    "Camila Barbosa",
    "Rafael dos Santos",
    "Amanda Silva Costa",
    "Bruno Henrique Oliveira",
    "Isabella Souza Lima",
    "Diego Rodrigues Santos",
    "Larissa Fernandes Silva",
    "Matheus Costa Oliveira",
    "Beatriz Santos Lima",
    "Thiago Almeida Costa"
]

FACULDADES = [
    "Faculdade de Medicina UFMG",
    "Faculdade de Direito PUC Minas",
    "Faculdade de Engenharia UEMG",
    "Faculdade de Administração Newton Paiva",
    "Faculdade de Arquitetura Una",
    "Faculdade de Computação CEFET-MG",
    "Faculdade de Odontologia UFMG",
    "Faculdade de Veterinária PUC Minas",
    "Faculdade de Psicologia Fumec",
    "Faculdade de Nutrição UNA",
    "Faculdade de Enfermagem UFMG",
    "Faculdade de Farmácia UEMG",
    "Faculdade de Fisioterapia Newton Paiva",
    "Faculdade de Design Belas Artes",
    "Faculdade de Jornalismo PUC Minas"
]

SEMESTRES = ["2025/1", "2025/2", "2026/1"]

STATUS_OPTIONS = ["Ativo", "Em Andamento", "Finalizado"]

async def popular_database():
    """Popula o banco de dados com dados fictícios"""
    
    # Conectar ao MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔄 Iniciando população do banco de dados...")
    
    # Limpar dados antigos (opcional)
    # await db.contratos.delete_many({})
    # await db.projetos.delete_many({})
    # await db.tarefas.delete_many({})
    # print("✅ Banco de dados limpo")
    
    contratos_criados = 0
    
    # Criar 15 contratos fictícios
    for i in range(15):
        # Gerar dados aleatórios
        cliente = random.choice(CLIENTES)
        faculdade = random.choice(FACULDADES)
        semestre = random.choice(SEMESTRES)
        
        # Datas aleatórias
        dias_inicio = random.randint(1, 60)
        duracao = random.randint(60, 120)
        data_inicio = datetime.utcnow() - timedelta(days=dias_inicio)
        data_fim = data_inicio + timedelta(days=duracao)
        
        # Valor entre R$ 3.000 e R$ 15.000
        valor = round(random.uniform(3000, 15000), 2)
        
        # Status aleatório
        status = random.choice(STATUS_OPTIONS)
        
        # Criar contrato
        contrato_id = str(uuid.uuid4())
        projeto_id = str(uuid.uuid4())
        
        contrato = {
            "id": contrato_id,
            "numero_contrato": 1000 + i,
            "cliente": cliente,
            "faculdade": faculdade,
            "semestre": semestre,
            "valor": valor,
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat(),
            "status": status,
            "projeto_id": projeto_id,
            "logs": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Inserir contrato
        await db.contratos.insert_one(contrato)
        
        # Criar projeto vinculado
        # Determinar etapa baseado no status
        if status == "Ativo":
            etapa = "1 - Lançamento do Contrato"
            macro_etapa = "Atendimento"
            progresso = random.uniform(0, 20)
        elif status == "Em Andamento":
            etapas_meio = [
                "4 - Criação (1ª e 2ª AP)",
                "5 - Conferência do Layout",
                "6 - Criação (3ª e 4ª AP)",
                "8 - Planejamento de Produção"
            ]
            etapa = random.choice(etapas_meio)
            macro_etapa = random.choice(["Criação", "Pré-Produção"])
            progresso = random.uniform(20, 80)
        else:  # Finalizado
            etapa = "14 - Contrato Encerrado"
            macro_etapa = "Pós-Vendas"
            progresso = 100.0
        
        # Determinar risco
        dias_restantes = (data_fim - datetime.utcnow()).days
        if dias_restantes < 7:
            risco = "Alto"
        elif dias_restantes < 20:
            risco = "Médio"
        else:
            risco = "Baixo"
        
        projeto = {
            "id": projeto_id,
            "contrato_id": contrato_id,
            "etapa_atual": etapa,
            "macro_etapa": macro_etapa,
            "progresso": round(progresso, 2),
            "risco": risco,
            "data_entrega": data_fim.isoformat(),
            "responsavel_atendimento": "Keyla Nascimento",
            "responsavel_designer": "Marcos Letro",
            "logs": [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Inserir projeto
        await db.projetos.insert_one(projeto)
        
        contratos_criados += 1
        print(f"✅ Contrato {i+1}/15: {cliente} - {faculdade} - R$ {valor:.2f}")
    
    # Estatísticas
    total_contratos = await db.contratos.count_documents({})
    total_projetos = await db.projetos.count_documents({})
    
    print(f"\n🎉 População concluída!")
    print(f"📊 Total de contratos no banco: {total_contratos}")
    print(f"📊 Total de projetos no banco: {total_projetos}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(popular_database())
