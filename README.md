# IDEIABH - Sistema de Gestão Operacional

<div align="center">

**Motor Inteligente de Gestão Operacional, Workflow e Governança de Projetos**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-19.0-61DAFB?logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb)](https://www.mongodb.com/)

</div>

---

## 🎯 Sobre o Projeto

**IDEIABH** é um sistema completo de gestão operacional para gerenciar todo o ciclo de vida de projetos. Implementa uma esteira de produção com 25 atividades organizadas em 7 macro etapas.

### Principais Diferenciais

- ✅ **Esteira Visual** - 3 colunas (Pré-Produção, Produção, Pós-Produção)
- ✅ **Kanban Drag-and-Drop** - Interface estilo Trello
- ✅ **Geração Progressiva** - Tarefas criadas conforme projeto avança
- ✅ **Gestão de Risco** - Calcula criticidade por prazo
- ✅ **Dashboard em Tempo Real** - KPIs atualizados
- ✅ **Validação Rigorosa** - Impede pulos de etapas

---

## 🚀 Funcionalidades Principais

### 1. Contratos
- Criar, editar, visualizar e excluir
- **Botão Aprovar** - Inicia projeto e gera tarefas
- **Botão Finalizar** - Valida conclusão
- Status: Ativo → Em Andamento → Finalizado

### 2. Esteira de Projetos
- Visualização em 3 colunas verticais
- Cards com progresso, dias restantes e risco
- Indicadores de criticidade:
  - 🔴 < 7 dias (CRÍTICO)
  - 🟡 8-15 dias (ATENÇÃO)
  - 🟢 > 15 dias (NORMAL)

### 3. Kanban de Tarefas
- Drag-and-drop estilo Trello
- 10 colunas de etapas
- Atualização automática de progresso

### 4. Dashboard
- KPIs em tempo real
- Projetos por status
- Tarefas atrasadas
- Gargalos por responsável

---

## 🛠️ Tecnologias

- **Backend**: FastAPI + Python 3.11
- **Frontend**: React 19 + Shadcn/UI + Tailwind
- **Database**: MongoDB 7.0
- **Drag & Drop**: @hello-pangea/dnd

---

## 📦 Instalação Rápida

### 1. Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edite .env com suas configurações
```

### 2. Frontend
```bash
cd frontend
yarn install
cp .env.example .env
```

### 3. Iniciar
```bash
# Backend
uvicorn server:app --host 0.0.0.0 --port 8001

# Frontend (outro terminal)
yarn start
```

Acesse: http://localhost:3000

---

## 📚 Documentação Completa

Consulte [DOCUMENTACAO_COMPLETA.md](DOCUMENTACAO_COMPLETA.md) para:
- Arquitetura detalhada
- Todos os endpoints da API
- Fluxo completo de uso
- Esteira de 25 atividades
- Regras de negócio

---

## 🎨 Fluxo de Uso

1. **Criar Contrato** → Sistema gera projeto + tarefas iniciais
2. **Aprovar Contrato** → Avança para Ativação + gera novas tarefas
3. **Ver Esteira** → Acompanha projeto nas 3 colunas
4. **Kanban** → Arrasta tarefas entre etapas
5. **Finalizar** → Valida conclusão e encerra

---

## 🧪 Testes

✅ **100% de cobertura** - 37/37 testes passando
- Criação de contratos
- Aprovação e finalização
- Avanço de etapas
- Geração de tarefas
- Dashboard e KPIs

---

## 📞 Suporte

- Email: suporte@ideiabh.com
- Issues: GitHub Issues

---

<div align="center">

**Feito com ❤️ pela equipe IDEIABH**

</div>
