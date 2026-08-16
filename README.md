# BoletoHub

Sistema para captura, organização e monitoramento de boletos recebidos por e-mail (via IMAP) ou cadastrados manualmente (formulário ou upload de PDF).

## Stack

- **Backend:** FastAPI (Python 3.11+), async/await, Pydantic v2, SQLAlchemy 2.0 (async) + Alembic
- **Banco de dados:** PostgreSQL 15
- **Fila/Cache:** Redis
- **Processamento assíncrono:** Celery (worker + beat)
- **Extração de PDF:** pdfplumber (texto selecionável) com fallback OCR via pytesseract + pdf2image
- **Autenticação:** JWT (e-mail + senha)
- **Frontend:** Next.js 14 (App Router) + Tailwind CSS + componentes no estilo shadcn/ui

## Como funciona

1. Cada usuário cria uma conta (e-mail + senha) e faz login — a sessão é um JWT armazenado em cookie.
2. Boletos podem ser adicionados de três formas:
   - **Manualmente**, preenchendo o formulário.
   - **Upload de PDF**, com extração automática de valor, vencimento, linha digitável e beneficiário.
   - **Escaneamento de e-mail**, disparado pelo botão "Escanear e-mails" no dashboard (ou automaticamente pelo Celery Beat), que varre as caixas IMAP cadastradas em "Contas de e-mail" em busca de e-mails com anexos PDF e assunto relacionado a boleto/fatura/cobrança/pagamento. Cada usuário pode cadastrar quantas contas quiser; os boletos de todas aparecem juntos no dashboard.
   - PDFs protegidos por senha (do scan de e-mail ou de upload manual) também são adicionados, marcados como "protegido por senha" — a senha é informada depois, na tela do boleto, para extrair os dados.
3. Um job diário (Celery Beat) marca como "vencido" todo boleto pendente cuja data de vencimento já passou.

> **Nota sobre o scanner de e-mail:** além das contas cadastradas por usuário (tabela `email_accounts`, senha criptografada em repouso), ainda é possível configurar uma caixa legada global via `IMAP_*` no `.env` — ela é escaneada em conjunto com as contas de cada usuário. O escaneamento manual (`POST /boletos/scan`) atribui os boletos encontrados ao usuário autenticado que disparou a ação; o escaneamento periódico automático roda para todo usuário com pelo menos uma conta de e-mail cadastrada (ou, na ausência de qualquer conta cadastrada, atribui a caixa legada ao primeiro usuário marcado como `is_superuser`).

## Estrutura do projeto

```
BoletoHub/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/0001_initial.py
│   ├── app/
│   │   ├── main.py            # entrypoint FastAPI
│   │   ├── config.py          # settings (pydantic-settings)
│   │   ├── database.py        # engine/session async SQLAlchemy
│   │   ├── celery_app.py      # instância Celery + beat schedule
│   │   ├── tasks.py           # scan de e-mail + atualização de vencidos
│   │   ├── models/            # User, Boleto, ScanLog
│   │   ├── schemas/           # Pydantic (user, boleto, scan)
│   │   ├── routers/           # auth, boletos, health
│   │   ├── services/          # auth, boleto, pdf_parser, email (IMAP)
│   │   ├── dependencies/      # get_current_user
│   │   └── utils/             # regex de extração de boletos
│   └── tests/                 # pytest (auth, boletos, pdf_parser)
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── middleware.ts          # protege /dashboard e /boletos
    ├── types/
    ├── lib/                   # api.ts (axios), auth.tsx (contexto)
    ├── components/            # Navbar, BoletoTable, ScanButton, etc.
    └── app/
        ├── login/, register/
        ├── dashboard/
        └── boletos/novo/, boletos/[id]/
```

## Modelos de dados

- **User**: usuários da aplicação (login por e-mail/senha, JWT).
- **Boleto**: boletos capturados, com `status` (`pendente`, `pago`, `vencido`) e `origem` (`email`, `manual`).
- **ScanLog**: histórico de varreduras de e-mail (sucesso, erro, ignorado), vinculado opcionalmente a um boleto.

## Pré-requisitos

- Docker e Docker Compose
- (Opcional, para desenvolvimento local sem Docker) Python 3.11+, Node.js 20+, PostgreSQL 15, Redis

## Setup rápido (Docker)

1. Copie o arquivo de variáveis de ambiente:

   ```bash
   cp .env.example .env
   ```

2. Ajuste os valores no `.env`:
   - `JWT_SECRET_KEY` / `SECRET_KEY`: gere segredos aleatórios (ex. `openssl rand -hex 32`).
   - `IMAP_USER` / `IMAP_PASSWORD`: credenciais da caixa de e-mail a ser escaneada.

3. Suba os containers:

   ```bash
   docker compose up --build
   ```

4. Rode as migrations do banco (em outro terminal, com os containers no ar):

   ```bash
   docker compose exec api alembic upgrade head
   ```

5. Acesse:
   - API: http://localhost:8000 (docs em `/docs`)
   - Frontend: http://localhost:3000

### Configurando o Gmail para o scanner IMAP

O Gmail exige uma **senha de app** (não a senha normal da conta) para acesso IMAP:

1. Ative a verificação em duas etapas na conta Google.
2. Acesse https://myaccount.google.com/apppasswords e gere uma senha de app.
3. Em Configurações do Gmail → Encaminhamento e POP/IMAP, habilite o IMAP.
4. Use o e-mail completo em `IMAP_USER` e a senha de app gerada em `IMAP_PASSWORD`.

## Desenvolvimento local (sem Docker)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# suba Postgres e Redis localmente ou aponte DATABASE_URL/REDIS_URL para instâncias existentes
alembic upgrade head
uvicorn app.main:app --reload
```

Para rodar o Celery localmente:

```bash
celery -A app.celery_app worker --loglevel=info
celery -A app.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testes

### Backend (pytest)

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

Os testes usam SQLite em memória (não precisam de Postgres/Redis rodando) e cobrem autenticação, CRUD de boletos (incluindo isolamento entre usuários) e extração de dados de PDF.

Também é possível rodar dentro do container:

```bash
docker compose build api
docker compose run --rm api pytest -v
```

### Frontend

```bash
cd frontend
npx tsc --noEmit   # checagem de tipos
npm run build      # build de produção
```

## Migrations (Alembic)

Criar uma nova migration a partir de alterações nos models:

```bash
docker compose exec api alembic revision --autogenerate -m "descricao da mudanca"
docker compose exec api alembic upgrade head
```

## Variáveis de ambiente

Veja `.env.example` para a lista completa. Principais grupos:

- **App**: `APP_NAME`, `APP_ENV`, `DEBUG`, `SECRET_KEY`
- **Banco**: `DATABASE_URL` (formato `postgresql+asyncpg://...`)
- **Redis/Celery**: `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- **IMAP**: `IMAP_HOST`, `IMAP_PORT`, `IMAP_USER`, `IMAP_PASSWORD`, `EMAIL_SCAN_INTERVAL_MINUTES`
- **JWT**: `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- **Frontend**: `NEXT_PUBLIC_API_URL`

## Problemas conhecidos

- O pacote `next@14.2.15` usado neste projeto possui vulnerabilidades conhecidas reportadas via `npm audit` (corrigidas apenas em major releases mais recentes, ex. Next 16). Uma migração para uma versão mais recente do Next.js não foi feita aqui por ser uma mudança de maior porte (breaking changes no App Router); avalie o upgrade antes de ir para produção.
