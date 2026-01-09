"""
Script para criar tarefas fictícias para os projetos
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

RESPONSAVEIS = [
    "Keyla Nascimento",
    "Marcos Letro",
    "Ana Paula Designer",
    "Bruno Criativo",
    "Carolina Atendimento",
    "Rafael Produção"
]

STATUS_TAREFAS = ["Pendente", "Em Andamento", "Concluído", "Atrasado"]

ATIVIDADES_POR_ETAPA = {
    "1 - Lançamento do Contrato": [
        {"numero": 1, "atividade": "Lançamento do Contrato", "setor": "Atendimento", "macro": "Atendimento"}
    ],
    "2 - Ativação do Projeto": [
        {"numero": 2, "atividade": "Apresentação do Projeto", "setor": "Atendimento", "macro": "Atendimento"},
        {"numero": 3, "atividade": "Agendamento de Criação", "setor": "Atendimento", "macro": "Atendimento"},
        {"numero": 4, "atividade": "Reunião de Criação", "setor": "Criação", "macro": "Atendimento"}
    ],
    "4 - Criação (1ª e 2ª AP)": [
        {"numero": 8, "atividade": "Criação", "setor": "Criação", "macro": "Criação"},
        {"numero": 9, "atividade": "1ª Apresentação do Convite", "setor": "Criação", "macro": "Criação"},
        {"numero": 10, "atividade": "1º Ajuste", "setor": "Criação", "macro": "Criação"},
        {"numero": 11, "atividade": "2ª Apresentação do Convite", "setor": "Criação", "macro": "Criação"},
        {"numero": 12, "atividade": "2º Ajuste", "setor": "Criação", "macro": "Criação"}
    ],
    "5 - Conferência do Layout": [
        {"numero": 13, "atividade": "Conferência do Layout", "setor": "Atendimento", "macro": "Criação"}
    ],
    "6 - Criação (3ª e 4ª AP)": [
        {"numero": 15, "atividade": "3ª Apresentação do Convite", "setor": "Criação", "macro": "Criação"},
        {"numero": 16, "atividade": "3º Ajuste", "setor": "Criação", "macro": "Criação"},
        {"numero": 17, "atividade": "4ª Apresentação do Convite", "setor": "Criação", "macro": "Criação"},
        {"numero": 18, "atividade": "4º Ajuste", "setor": "Criação", "macro": "Criação"}
    ],
    "8 - Planejamento de Produção": [
        {"numero": 20, "atividade": "Planejamento de Produção", "setor": "Produção", "macro": "Pré-Produção"}
    ]
}

async def criar_tarefas():
    """Cria tarefas para os projetos existentes"""
    
    # Conectar ao MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔄 Criando tarefas para os projetos...")
    
    # Buscar todos os projetos
    projetos = await db.projetos.find({}, {"_id": 0}).to_list(1000)
    
    tarefas_criadas = 0
    
    for projeto in projetos:
        etapa_atual = projeto.get('etapa_atual')
        projeto_id = projeto.get('id')
        data_entrega = datetime.fromisoformat(projeto.get('data_entrega').replace('Z', ''))
        
        # Buscar atividades para esta etapa
        atividades = ATIVIDADES_POR_ETAPA.get(etapa_atual, [])
        
        if not atividades:
            continue
        
        # Criar tarefas para esta etapa
        for idx, ativ_info in enumerate(atividades):
            tarefa_id = str(uuid.uuid4())
            
            # Calcular prazo baseado na data de entrega
            dias_antes = len(atividades) - idx
            prazo = data_entrega - timedelta(days=dias_antes * 5)
            
            # Determinar status
            if prazo < datetime.utcnow():
                status = random.choice(["Atrasado", "Concluído"])
            else:
                status = random.choice(["Pendente", "Em Andamento", "Concluído"])
            
            data_conclusao = None
            if status == "Concluído":
                data_conclusao = prazo - timedelta(days=random.randint(0, 3))
            
            tarefa = {
                "id": tarefa_id,
                "projeto_id": projeto_id,
                "etapa": etapa_atual,
                "macro_etapa": ativ_info["macro"],
                "numero": ativ_info["numero"],
                "atividade": ativ_info["atividade"],
                "setor": ativ_info["setor"],
                "titulo": ativ_info["atividade"],
                "descricao": f"Executar {ativ_info['atividade']} para o projeto",
                "responsavel": random.choice(RESPONSAVEIS),
                "prazo": prazo.isoformat(),
                "data_conclusao": data_conclusao.isoformat() if data_conclusao else None,
                "status": status,
                "dependencias": [],
                "critica": True,
                "logs": [],
                "created_at": datetime.utcnow().isoformat()
            }
            
            await db.tarefas.insert_one(tarefa)
            tarefas_criadas += 1
    
    # Estatísticas
    total_tarefas = await db.tarefas.count_documents({})
    
    print(f"\n🎉 Tarefas criadas com sucesso!")
    print(f"📊 Total de tarefas no banco: {total_tarefas}")
    print(f"✅ {tarefas_criadas} novas tarefas adicionadas")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(criar_tarefas())
