# FastAPI Auth Core

A production-ready FastAPI template with **passwordless authentication** using WebAuthn Passkeys.

## Features

- 🔑 **Passkeys (WebAuthn)**: Modern passwordless authentication using FIDO2
- 🔐 **Secure Sessions**: JWT tokens stored in HttpOnly cookies (XSS protection)
- 🔄 **Token Refresh**: Automatic access token renewal via refresh tokens
- 🗄️ **Async Database**: PostgreSQL with SQLAlchemy async ORM
- 🐳 **Docker Ready**: Complete Docker and Docker Compose setup
- 📦 **Modern Tooling**: Uses `uv` for fast dependency management
- 🔀 **Database Migrations**: Alembic for schema versioning
- 📝 **Structured Logging**: JSON format for production, readable for dev
- 🧪 **Test Suite**: pytest with async support (isolated test database)
- 📱 **Multi-Device**: Users can register multiple passkeys (phone, laptop, security key)
- ⚡ **Redis Cache**: Challenge storage with automatic expiration
- 🛡️ **Rate Limiting**: IP-based protection against DDoS attacks

---

## 🔑 How Passkeys Work

Passkeys are a modern, phishing-resistant authentication method that replaces passwords. They use public-key cryptography and biometric verification (Face ID, Touch ID, Windows Hello, or a security key).

### Authentication Flow

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Browser    │         │   Backend    │         │    Redis     │
└──────┬───────┘         └──────┬───────┘         └──────┬───────┘
       │                        │                        │
       │ 1. POST /register/begin│                        │
       │───────────────────────>│                        │
       │                        │ 2. Store challenge     │
       │                        │───────────────────────>│
       │   3. Return options    │                        │
       │<───────────────────────│                        │
       │                        │                        │
       │ 4. User creates passkey│                        │
       │   (biometric prompt)   │                        │
       │                        │                        │
       │ 5. POST /register/complete                      │
       │───────────────────────>│ 6. Get & verify        │
       │                        │    challenge           │
       │                        │<───────────────────────│
       │                        │                        │
       │   7. Set JWT cookies   │                        │
       │<───────────────────────│                        │
       │                        │                        │
```

### Why Passkeys?

| Traditional Auth | Passkeys |
|-----------------|----------|
| ❌ Passwords can be stolen | ✅ Private key never leaves device |
| ❌ Phishing attacks possible | ✅ Phishing-resistant by design |
| ❌ Password reuse across sites | ✅ Unique key per site |
| ❌ Need to remember passwords | ✅ Just use biometrics |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (recommended)

### Local Development

```bash
# 1. Clone and configure
git clone https://github.com/Federiko9811/fastapi-auth-core.git
cd fastapi-auth-core
cp .env.example .env

# 2. Generate a secure secret key
openssl rand -hex 32
# Paste the output in .env at SECRET_KEY=

# 3. Setup and run
make dev      # Install dependencies + pre-commit
make db       # Start PostgreSQL + Redis
make migrate  # Apply database migrations
make run      # Start server on http://localhost:8008
```

### Full Docker

```bash
cp .env.example .env
# Edit .env with your settings
docker compose up -d
docker compose exec app-api alembic upgrade head
```

---

## 📡 API Endpoints

### Passkeys (`/api/v1/passkeys`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register/begin` | Start passkey registration |
| POST | `/register/complete` | Complete registration & login |
| POST | `/login/begin` | Start authentication |
| POST | `/login/complete` | Complete login |
| GET | `/` | List user's passkeys (🔒) |
| PATCH | `/{id}` | Rename a passkey (🔒) |
| DELETE | `/{id}` | Delete a passkey (🔒) |

🔒 = Requires authentication

### Auth (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/refresh` | Refresh access token |
| POST | `/logout` | Clear cookies |

### Users (`/api/v1/users`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/me` | Current user profile (🔒) |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Quick status |
| GET | `/health` | Detailed health with DB check |

---

## 🛡️ Rate Limiting

The API includes IP-based rate limiting to protect against abuse:

- **Default**: 100 requests per 60 seconds per IP
- **Response headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **When exceeded**: Returns `429 Too Many Requests`

Configure in `.env`:
```bash
RATE_LIMIT_REQUESTS=100  # Max requests per window
RATE_LIMIT_WINDOW=60     # Window size in seconds
```

---

## 🚀 Production Deployment

### Required Configuration

Create a `.env` for production with these critical settings:

```bash
# Required: Generate with `openssl rand -hex 32`
SECRET_KEY=your-secure-random-key

# WebAuthn: Your production domain (NO protocol, NO port)
WEBAUTHN_RP_ID=yourdomain.com
WEBAUTHN_RP_NAME=Your App Name
WEBAUTHN_ORIGIN=https://yourdomain.com

# Database
POSTGRES_SERVER=db
POSTGRES_USER=youruser
POSTGRES_PASSWORD=strong-password
POSTGRES_DB=yourdb

# Redis (use service name in Docker)
REDIS_URL=redis://redis:6379

# Security (MUST be true for HTTPS)
COOKIE_SECURE=true

# CORS (your frontend URL)
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### ⚠️ Important Notes

1. **WEBAUTHN_RP_ID cannot change** after users create passkeys. Choose carefully!
2. **HTTPS is required** for passkeys to work in production (except localhost)
3. **COOKIE_SECURE=true** ensures cookies are only sent over HTTPS

### Deploy Steps

```bash
# 1. Copy your production .env to the server

# 2. Start services
docker compose up -d

# 3. Run migrations
docker compose exec app-api alembic upgrade head

# 4. Check health
curl https://yourdomain.com/health
```

---

## 🔧 Makefile Commands

| Command | Description |
|---------|-------------|
| `make dev` | Install deps + setup pre-commit |
| `make run` | Start dev server (reads APP_PORT from .env) |
| `make db` | Start PostgreSQL + Redis |
| `make migrate` | Apply migrations |
| `make test` | Run test suite |
| `make format` | Format code with Ruff |
| `make lint` | Check code style |
| `make clean` | Remove cache files |

---

## 📁 Project Structure

```
fastapi-auth-core/
├── app/
│   ├── api/
│   │   ├── deps.py              # Auth dependencies
│   │   └── v1/endpoints/
│   │       ├── auth.py          # Token refresh, logout
│   │       ├── passkey.py       # WebAuthn endpoints
│   │       └── user.py          # User profile
│   ├── core/
│   │   ├── cache.py             # Redis connection
│   │   ├── config.py            # Environment settings
│   │   ├── rate_limit.py        # Rate limiting middleware
│   │   ├── security.py          # JWT utilities
│   │   └── webauthn.py          # WebAuthn helpers
│   ├── models/
│   │   ├── user.py              # User model
│   │   └── passkey.py           # Passkey model
│   └── main.py                  # FastAPI app
├── alembic/                     # Database migrations
├── tests/                       # Test suite
├── docker-compose.yml
├── Dockerfile
└── Makefile
```

---

## ⚙️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | **required** |
| `POSTGRES_*` | Database connection | **required** |
| `WEBAUTHN_RP_ID` | Passkey domain | `localhost` |
| `WEBAUTHN_RP_NAME` | Shown in passkey prompts | `FastAPI Auth Core` |
| `WEBAUTHN_ORIGIN` | Frontend URL | `http://localhost:3000` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `COOKIE_SECURE` | HTTPS-only cookies | `false` |
| `RATE_LIMIT_REQUESTS` | Max requests per window | `100` |
| `RATE_LIMIT_WINDOW` | Window size (seconds) | `60` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |

---

## 🧪 Testing

Tests use an isolated database (`{POSTGRES_DB}_test`).

```bash
make db    # Ensure PostgreSQL is running
make test  # Run tests
```

---

## 📱 Frontend Integration

Use the [@simplewebauthn/browser](https://github.com/MasterKale/SimpleWebAuthn) library:

```bash
npm install @simplewebauthn/browser
```

Example registration flow:

```javascript
import { startRegistration } from '@simplewebauthn/browser';

// 1. Get options from backend
const { options } = await fetch('/api/v1/passkeys/register/begin', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com' })
}).then(r => r.json());

// 2. Create passkey (browser handles biometrics)
const credential = await startRegistration({ optionsJSON: options });

// 3. Complete registration
await fetch('/api/v1/passkeys/register/complete', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',  // Required for cookies
  body: JSON.stringify({ email: 'user@example.com', credential })
});
```

---

## License

MIT
