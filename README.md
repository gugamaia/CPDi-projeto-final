# 📄 Resume AI — Avaliador de Currículos com IA

![CI](https://github.com/SEU-USUARIO/resume-ai/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-green)

Projeto de formatura (CPDI) desenvolvido por **Alexandre Tourinho**, **Arthur Hass** e **Gustavo Maia**.

Uma API que recebe um currículo (texto ou arquivo) e usa **inteligência
artificial (Google Gemini)** para avaliá-lo automaticamente, devolvendo:

- 📊 **Nota geral** (0 a 100)
- ✅ **Pontos fortes**
- ❌ **Pontos fracos**
- 🔑 **Palavras-chave faltando** (aderência à vaga, se informada)
- 💡 **Dicas de melhoria**
- 🔐 **Login e cadastro** — cada avaliação fica vinculada à conta do usuário
- 🗂️ **Histórico de avaliações** — nenhum usuário perde as consultas já feitas

Inclui uma **interface web própria** (tema "correção de prova") para facilitar
a demonstração do projeto.

---

## 🧱 Stack técnica

| Camada         | Tecnologia                                   |
|----------------|-----------------------------------------------|
| API            | [FastAPI](https://fastapi.tiangolo.com/)      |
| Validação      | [Pydantic v2](https://docs.pydantic.dev/)     |
| Banco de dados | MongoDB (Atlas) + [Beanie](https://beanie-odm.dev/) (ODM assíncrono) |
| IA             | Google Gemini API (`gemini-1.5-flash`)        |
| Extração de arquivo | `pypdf`, `python-docx`                   |
| Autenticação   | JWT (`python-jose`) + hash de senha (`passlib`/`bcrypt`) |
| Frontend       | HTML + CSS + JS puro (sem framework)          |

A camada de IA (`app/services/ai_providers.py`) foi construída com um padrão
de **abstração de provedor**: existe também suporte pronto para OpenAI e
Claude, bastando trocar a variável `AI_PROVIDER` no `.env` — mas o projeto
roda **com Gemini por padrão**.

---

## 📂 Estrutura do projeto

```
resume-ai/
├── .github/
│   └── workflows/
│       └── ci.yml                  # valida sintaxe/import da API a cada push
├── backend/
│   ├── app/
│   │   ├── main.py                 # cria a aplicação FastAPI e serve o frontend
│   │   ├── config.py                # lê variáveis de ambiente (.env)
│   │   ├── database.py               # conexão com MongoDB via Beanie
│   │   ├── models/
│   │   │   ├── resume.py              # Document (Beanie) + Schemas (Pydantic) — histórico
│   │   │   └── user.py                # Document (Beanie) + Schemas de autenticação
│   │   ├── services/
│   │   │   ├── ai_providers.py         # integração com Gemini (+ OpenAI/Claude)
│   │   │   ├── resume_parser.py         # extrai texto de PDF/DOCX/TXT
│   │   │   ├── evaluator.py            # orquestra a chamada de IA
│   │   │   └── security.py             # hash de senha + geração/validação de JWT
│   │   └── routers/
│   │       ├── auth.py                  # cadastro, login, usuário atual
│   │       └── resume.py               # endpoints da API + histórico por usuário
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── index.html                  # interface web (login + avaliação + histórico)
├── postman/
│   └── resume-ai.postman_collection.json  # testa cadastro → login → avaliação → histórico
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🔌 Endpoints da API

### Autenticação

| Método | Rota                | Descrição                                   |
|--------|----------------------|-----------------------------------------------|
| `POST` | `/api/auth/register` | Cria uma conta e retorna o token JWT           |
| `POST` | `/api/auth/login`    | Autentica e retorna o token JWT                |
| `GET`  | `/api/auth/me`       | Retorna os dados do usuário autenticado        |

Todas as rotas de currículo abaixo exigem o header
`Authorization: Bearer <token>` obtido no login/cadastro.

### Currículos / Histórico (tabela `resumes`)

| Método   | Rota                          | Descrição                             |
|----------|--------------------------------|------------------------------------------|
| `POST`   | `/api/resumes/evaluate/text`  | Avalia um currículo (texto) e salva no histórico do usuário |
| `POST`   | `/api/resumes/evaluate/file`  | Avalia um currículo (arquivo `.pdf`/`.docx`/`.txt`) e salva no histórico |
| `GET`    | `/api/resumes/me/history`     | Lista todas as avaliações do usuário logado (mais recentes primeiro) |
| `GET`    | `/api/resumes/{id}`           | Busca uma avaliação específica do usuário logado |
| `DELETE` | `/api/resumes/{id}`           | Remove uma avaliação do histórico do usuário logado |
| `GET`    | `/api/health`                 | Health check                             |

Documentação interativa (Swagger) disponível em `/docs` assim que o servidor
estiver rodando.

### Modelo de dados — tabela `resumes` (histórico de feedbacks)

Cada avaliação gerada pela IA é salva como um documento na coleção
`resumes`, sempre vinculada ao `owner_id` do usuário logado:

| Campo            | Tipo                | Descrição                                      |
|-------------------|----------------------|---------------------------------------------------|
| `_id`             | ObjectId             | Identificador da avaliação                        |
| `owner_id`        | string                | Id do usuário dono (coleção `users`)              |
| `candidate_name`  | string (opcional)      | Nome do candidato                                 |
| `target_role`     | string (opcional)      | Vaga/área alvo informada                          |
| `raw_text`        | string                | Texto do currículo enviado                        |
| `evaluation`      | objeto                | `{ score, strengths[], weaknesses[], missing_keywords[], improvement_tips[], summary }` |
| `ai_provider`     | string                | Provedor de IA usado (`gemini`, `openai`, `claude`) |
| `created_at`      | datetime              | Data/hora da avaliação                            |

Essa estrutura é o que garante que **cada usuário tenha seu próprio
histórico de consultas**, consultável a qualquer momento via
`GET /api/resumes/me/history`.

---

## 🧪 Testando com Postman

O repositório inclui uma collection pronta em
[`postman/resume-ai.postman_collection.json`](postman/resume-ai.postman_collection.json)
que testa o fluxo completo, na ordem:

1. **Cadastro** — cria um usuário com e-mail único (gerado automaticamente a
   cada execução) e já retorna o token JWT.
2. **Login** — autentica com o e-mail/senha criados e atualiza o token salvo.
3. **Usuário logado (`/me`)** — confirma que o token é válido.
4. **Avaliar currículo (texto)** — envia um currículo de exemplo, aciona o
   Gemini e salva o resultado no histórico do usuário.
5. **Meu histórico** — lista as avaliações do usuário e confirma que a do
   passo 4 está lá.
6. **Buscar avaliação por ID** — busca o registro específico criado.
7. **Acesso sem token** — confirma que a rota retorna `401` sem
   `Authorization`, validando que o histórico é protegido.
8. **Remover avaliação** — apaga o registro de teste (`204`).
9. **Confirma remoção** — busca de novo e espera `404`.

Cada request já vem com testes automáticos (aba *Tests* do Postman,
via `pm.test`), então é possível rodar tudo de uma vez pelo **Collection
Runner** e ver o relatório de sucesso/falha de cada etapa.

### Como usar

1. Abra o Postman → **Import** → selecione o arquivo
   `postman/resume-ai.postman_collection.json`.
2. Confirme que a variável de collection `baseUrl` aponta para onde a API
   está rodando (padrão: `http://localhost:8000`).
3. Rode o servidor (`uvicorn app.main:app --reload`).
4. Execute os requests em ordem (1 → 9) manualmente, ou use **Collection
   Runner** para rodar tudo de uma vez.

> As variáveis `accessToken` e `resumeId` são preenchidas automaticamente
> pelos scripts de teste de cada request — não é preciso copiar/colar nada
> manualmente entre as chamadas.

---

## 🚀 Como rodar o projeto localmente

### Pré-requisitos
- Python 3.11+
- Uma conta gratuita no [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
- Uma chave de API do [Google AI Studio (Gemini)](https://aistudio.google.com/apikey) — gratuita

### 1. Clonar o repositório

```bash
git clone https://github.com/<seu-usuario>/resume-ai.git
cd resume-ai
```

### 2. Criar o banco no MongoDB Atlas (gratuito)

1. Acesse https://www.mongodb.com/cloud/atlas/register e crie uma conta.
2. Crie um **Project** e, dentro dele, um **Cluster M0 (Free)**.
3. Em **Database Access**, crie um usuário e senha (anote os dois).
4. Em **Network Access**, clique em **Add IP Address → Allow Access from
   Anywhere** (`0.0.0.0/0`) — suficiente para o projeto de formatura.
5. Em **Database → Connect → Drivers**, copie a *connection string*:
   ```
   mongodb+srv://usuario:senha@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### 3. Obter a chave do Gemini

1. Acesse https://aistudio.google.com/apikey
2. Clique em **Create API key** e copie o valor gerado.

### 4. Configurar variáveis de ambiente

```bash
cd backend
cp .env.example .env
```

Edite o arquivo `.env`:

```bash
MONGODB_URI=mongodb+srv://usuario:senha@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=resume_ai

AI_PROVIDER=gemini
GEMINI_API_KEY=coloque_sua_chave_aqui
GEMINI_MODEL=gemini-1.5-flash

JWT_SECRET_KEY=coloque_uma_chave_aleatoria_aqui
```

> Gere uma chave aleatória com:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 5. Instalar dependências e rodar

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Acesse:
- Interface web: **http://localhost:8000**
- Documentação da API: **http://localhost:8000/docs**

---

## 🐙 Passo a passo completo para publicar no GitHub

Este pacote já vem com o repositório Git **inicializado localmente** (branch
`main`, com commits do histórico do projeto). Falta só criar o repositório
remoto no GitHub e enviar (`push`).

### Opção A — Pelo site do GitHub

1. Acesse [github.com/new](https://github.com/new)
2. **Repository name**: `resume-ai`
3. **Description** (sugestão):
   > API com FastAPI + MongoDB (Beanie) que usa IA (Gemini) para avaliar currículos, com login e histórico por usuário — projeto de formatura CPDI
4. Escolha **Public** (para constar no portfólio) ou **Private**
5. **Não marque** nenhuma opção de "Add a README/.gitignore/license" — já temos todos
6. Clique em **Create repository**
7. O GitHub vai mostrar uma tela com comandos. Use a seção **"…or push an
   existing repository from the command line"**:

```bash
cd resume-ai
git remote add origin https://github.com/<seu-usuario>/resume-ai.git
git push -u origin main
```

### Opção B — Pelo terminal com GitHub CLI (`gh`)

Se tiver o [GitHub CLI](https://cli.github.com/) instalado e autenticado
(`gh auth login`), o repositório remoto é criado e o push feito em um único
comando:

```bash
cd resume-ai
gh repo create resume-ai --public --source=. --remote=origin --push
```

### 5. Confirmar que subiu certo

Acesse `https://github.com/<seu-usuario>/resume-ai` e confira se aparecem:
- [ ] `README.md` renderizado na página inicial do repositório
- [ ] As pastas `backend/`, `frontend/`, `postman/` e `.github/workflows/`
- [ ] O arquivo `backend/.env` **não** aparece na lista (só o `.env.example`)
- [ ] Aba **Actions** com o workflow `CI` rodando (✅ verde) — validação
  automática de sintaxe, import da API e da collection do Postman a cada push

> ⚠️ O `.env` real **nunca** é enviado ao GitHub (já está no `.gitignore`).
> Cada integrante do grupo, ou o professor ao rodar o projeto, deve criar o
> próprio `.env` a partir do `backend/.env.example`.

### 6. Ajustar o badge do README

No topo do `README.md`, troque `SEU-USUARIO` pelo usuário/organização real do
GitHub para o badge de CI funcionar:

```markdown
![CI](https://github.com/<seu-usuario>/resume-ai/actions/workflows/ci.yml/badge.svg)
```

### 7. Convidar os colegas de grupo (opcional)
No GitHub: **Settings → Collaborators → Add people** e adicione os outros
integrantes para que todos possam commitar diretamente.

### 8. Fluxo de trabalho em grupo (sugestão)

```bash
# Antes de começar a mexer, sempre atualizar:
git pull origin main

# Criar uma branch por funcionalidade:
git checkout -b feature/exportar-pdf

# Depois de codar:
git add .
git commit -m "Adiciona exportação do parecer em PDF"
git push origin feature/exportar-pdf

# Depois, abrir um Pull Request no GitHub para revisar e mesclar com a main
# (o CI roda automaticamente no PR e mostra se algo quebrou)
```

---
```bash
## 🎤 Roteiro sugerido para o pitch (3–5 min)

1. **Grupo** (15s): quem são vocês.
2. **Problema** (30s): candidatos não sabem se o currículo está bom antes de
   enviar para uma vaga.
3. **Solução** (30s): API + IA que dá nota e feedback instantâneo.
4. **Demo ao vivo** (2 min): colar/enviar um currículo real, mostrar nota,
   pontos fortes/fracos, palavras-chave e dicas aparecendo na tela.
5. **Stack técnica** (30s): FastAPI, Pydantic, MongoDB/Beanie, Gemini —
   arquitetura pronta para trocar de provedor de IA.
6. **Próximos passos** (15s): multilinguagem, comparação com vaga, exportar PDF.
```
---

## 🗺️ Próximos passos (backlog)

- [ ] Suporte a multilinguagem (avaliar currículo em outro idioma)
- [ ] Comparar currículo com uma descrição de vaga colada pelo usuário
- [ ] Exportar o parecer em PDF
- [ ] Recuperação de senha por e-mail

---

## 👥 Equipe

- Alexandre Tourinho
- Arthur Hass
- Gustavo Maia

Projeto desenvolvido para a disciplina/atividade de formatura — CPDI.
