# FastAPI Auth Core

A production-ready FastAPI template with JWT authentication using HttpOnly cookies.

## Features

- 🔐 **Secure Authentication**: JWT tokens stored in HttpOnly cookies (XSS protection)
- 🔄 **Token Refresh**: Automatic access token renewal via refresh tokens
- 🗄️ **Async Database**: PostgreSQL with SQLAlchemy async ORM
- 🐳 **Docker Ready**: Complete Docker and Docker Compose setup
- 📦 **Modern Tooling**: Uses `uv` for fast dependency management
- 🔒 **Password Hashing**: Argon2id (industry recommended)
- 🔀 **Database Migrations**: Alembic for schema versioning
- 📝 **Structured Logging**: JSON format for production, readable for dev
- ✅ **Password Validation**: Min 8 chars, uppercase, lowercase, digit
- 🧪 **Test Suite**: pytest with async support (isolated test database)

---

## 🚀 Usare come Template per un Nuovo Progetto

Questa sezione spiega come clonare questo repository e configurarlo per un nuovo progetto.

### Step 1: Clona il Repository

```bash
# Clona con un nuovo nome (sostituisci "my-new-api" con il nome del tuo progetto)
git clone https://github.com/Federiko9811/fastapi-auth-core.git my-new-api
cd my-new-api

# Rimuovi la history git e inizializza un nuovo repository
rm -rf .git
git init
```

### Step 2: Rinomina il Progetto

Devi aggiornare il nome del progetto in questi file:

| File | Cosa cambiare |
|------|---------------|
| `pyproject.toml` | `name = "my-new-api"` |
| `app/core/config.py` | `PROJECT_NAME: str = "My New API"` |
| `.env.example` | `PROJECT_NAME=My New API` |
| `.env.example` | `POSTGRES_DB=my_new_api_db` |
| `docker-compose.yml` | Container names (opzionale) |
| `README.md` | Titolo e descrizione |

**Esempio con sed (Linux/Mac):**

```bash
# Sostituisci "fastapi-auth-core" con "my-new-api" in pyproject.toml
sed -i 's/fastapi-auth-core/my-new-api/g' pyproject.toml

# Aggiorna il nome del progetto in config.py
sed -i 's/FastAPI Auth Core/My New API/g' app/core/config.py

# Aggiorna .env.example
sed -i 's/FastAPI Auth Core/My New API/g' .env.example
sed -i 's/POSTGRES_DB=auth_db/POSTGRES_DB=my_new_api_db/g' .env.example
```

### Step 3: Configura l'Ambiente

```bash
# Copia e configura le variabili d'ambiente
cp .env.example .env

# Genera una SECRET_KEY sicura
openssl rand -hex 32
# Copia l'output e incollalo nel file .env alla riga SECRET_KEY=
```

### Step 4: Setup Sviluppo

```bash
# Installa dipendenze e pre-commit hooks
make dev

# Avvia il database PostgreSQL
make db

# Attendi qualche secondo che il DB sia pronto, poi crea le tabelle
make migrate
```

### Step 5: Primo Avvio!

```bash
# Avvia il server di sviluppo
make run
```

🎉 **Il server è attivo!**
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/api/v1/docs
- Registra un utente: `POST /api/v1/auth/register`

### Step 6: Primo Commit

```bash
git add .
git commit -m "Initial commit: My New API"
```

---

## Quick Start (Senza Clonazione)

Se stai lavorando direttamente su questo repository:

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (recommended for local development)

### Option 1: Full Docker (Simplest)

Run everything in containers:

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env - generate SECRET_KEY with: openssl rand -hex 32

# 2. Start all services
docker-compose up -d

# 3. Run migrations
docker-compose exec app-api uv run alembic upgrade head

# API available at http://localhost:8000
```

### Option 2: Local Development (Recommended)

Run the database in Docker, app locally for hot-reload:

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env - generate SECRET_KEY with: openssl rand -hex 32

# 2. Setup development environment
make dev  # Installs dependencies + pre-commit hooks

# 3. Start database
make db

# 4. Run migrations and start server
make migrate
make run

# API available at http://localhost:8000
```

---

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make dev` | Install dependencies + setup pre-commit hooks |
| `make install` | Install production dependencies only |
| `make run` | Start development server |
| `make test` | Run test suite |
| `make lint` | Check code style with Ruff |
| `make format` | Format code with Ruff |
| `make db` | Start database container |
| `make migrate` | Apply database migrations |
| `make migration msg="..."` | Create new migration |
| `make clean` | Remove cache files |

## Database Migrations

Alembic manages database schema changes.

### Common Commands

```bash
# Apply all pending migrations
make migrate

# Create a new migration after modifying models
make migration msg="Add phone field to users"

# Manual commands (if not using Makefile)
POSTGRES_SERVER=localhost uv run alembic upgrade head
POSTGRES_SERVER=localhost uv run alembic revision --autogenerate -m "Description"
```

### Workflow Example

1. **Modify a model** (e.g., add a field to `User`):
   ```python
   # app/models/user.py
   phone: Mapped[str | None] = mapped_column(String, nullable=True)
   ```

2. **Generate migration**:
   ```bash
   make migration msg="Add phone to users"
   ```

3. **Review the generated file** in `alembic/versions/`

4. **Apply migration**:
   ```bash
   make migrate
   ```

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint    | Description                          |
|--------|-------------|--------------------------------------|
| POST   | `/register` | Register a new user                  |
| POST   | `/login`    | Login and receive cookies            |
| POST   | `/refresh`  | Refresh access token                 |
| POST   | `/logout`   | Clear authentication cookies         |

### Users (`/api/v1/users`)

| Method | Endpoint | Description                          |
|--------|----------|--------------------------------------|
| GET    | `/me`    | Get current user profile             |

### Health Check

| Method | Endpoint  | Description                          |
|--------|-----------|--------------------------------------|
| GET    | `/`       | Quick status check                   |
| GET    | `/health` | Detailed status with DB connectivity |

### API Documentation

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## Project Structure

```
fastapi-auth-core/
├── alembic/                  # Database migrations
│   ├── versions/             # Migration files
│   └── env.py                # Alembic configuration
├── app/
│   ├── api/
│   │   ├── deps.py           # Dependency injection (auth)
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py   # Auth endpoints
│   │       │   └── user.py   # User endpoints
│   │       └── router.py     # API router
│   ├── core/
│   │   ├── config.py         # Settings from env vars
│   │   ├── exceptions.py     # Custom HTTP exceptions
│   │   ├── logging.py        # Structured logging
│   │   └── security.py       # JWT & password utilities
│   ├── db/
│   │   ├── base.py           # SQLAlchemy base class
│   │   └── session.py        # Database session
│   ├── models/
│   │   └── user.py           # User SQLAlchemy model
│   ├── schemas/
│   │   ├── token.py          # Token response schemas
│   │   └── user.py           # Pydantic schemas
│   └── main.py               # FastAPI application
├── tests/                    # Test suite (uses isolated test DB)
├── Makefile                  # Development commands
├── .pre-commit-config.yaml   # Pre-commit hooks
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env.example
```

## Environment Variables

| Variable                      | Description                    | Default              |
|-------------------------------|--------------------------------|----------------------|
| `PROJECT_NAME`                | Application display name       | FastAPI Application  |
| `API_V1_STR`                  | API version prefix             | /api/v1              |
| `BACKEND_CORS_ORIGINS`        | Allowed CORS origins           | localhost:3000,8080  |
| `POSTGRES_SERVER`             | Database host                  | db                   |
| `POSTGRES_USER`               | Database user                  | -                    |
| `POSTGRES_PASSWORD`           | Database password              | -                    |
| `POSTGRES_DB`                 | Database name                  | -                    |
| `SECRET_KEY`                  | JWT signing key                | -                    |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime          | 15                   |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Refresh token lifetime         | 7                    |

## Password Requirements

When registering, passwords must meet these requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

## Testing

I test usano un database isolato (`{POSTGRES_DB}_test`) che viene creato prima dei test e eliminato dopo. Il database di sviluppo/produzione non viene mai toccato.

```bash
# Assicurati che il DB sia attivo
make db

# Esegui i test
make test
```

## License

MIT
