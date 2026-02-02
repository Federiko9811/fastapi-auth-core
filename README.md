# FastAPI Auth Core

A production-ready FastAPI template with **passwordless authentication** using WebAuthn Passkeys.

## Features

- 🔑 **Passkeys (WebAuthn)**: Modern passwordless authentication using FIDO2
- 🔐 **Secure Sessions**: JWT tokens stored in HttpOnly cookies (XSS protection)
- 🔄 **Token Refresh**: Automatic access token renewal via refresh tokens
- 🗄️ **Async Database**: PostgreSQL with SQLAlchemy async ORM
- 🐳 **Docker Ready**: Separate compose files for dev and production
- 📦 **Modern Tooling**: Uses `uv` for fast dependency management
- 🔀 **Database Migrations**: Alembic for schema versioning
- 📝 **Structured Logging**: JSON format for production, readable for dev
- 🧪 **Test Suite**: pytest with async support (isolated test database)
- 📱 **Multi-Device**: Users can register multiple passkeys with OTP email verification
- ⚡ **Redis Cache**: Challenge and OTP storage with automatic expiration
- 🛡️ **Rate Limiting**: IP-based protection against DDoS attacks
- 📧 **Email OTP**: Secure verification when adding passkeys to existing accounts

---

## 🔑 How Passkeys Work

Passkeys are a modern, phishing-resistant authentication method that replaces passwords. They use public-key cryptography and biometric verification (Face ID, Touch ID, Windows Hello, or a security key).

### Registration Flow

**New User:** Direct passkey registration

```
Browser                    Backend                    Redis
   │                          │                          │
   │ POST /register/begin     │                          │
   │─────────────────────────>│                          │
   │                          │ Store challenge          │
   │                          │─────────────────────────>│
   │   {options: {...}}       │                          │
   │<─────────────────────────│                          │
   │                          │                          │
   │ User creates passkey     │                          │
   │ (biometric prompt)       │                          │
   │                          │                          │
   │ POST /register/complete  │                          │
   │─────────────────────────>│                          │
   │                          │                          │
   │   JWT cookies set        │                          │
   │<─────────────────────────│                          │
```

**Existing User:** OTP verification required (prevents Account Takeover)

```
Browser                    Backend                    Redis/Email
   │                          │                          │
   │ POST /register/begin     │                          │
   │─────────────────────────>│                          │
   │                          │ Generate OTP             │
   │                          │─────────────────────────>│ Redis + Email
   │   {requires_otp: true}   │                          │
   │<─────────────────────────│                          │
   │                          │                          │
   │ POST /register/verify-otp│                          │
   │─────────────────────────>│ Verify OTP               │
   │                          │<─────────────────────────│
   │   {options: {...}}       │                          │
   │<─────────────────────────│                          │
   │                          │                          │
   │ Continue with passkey... │                          │
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
| POST | `/register/begin` | Start passkey registration (sends OTP if user exists) |
| POST | `/register/verify-otp` | Verify OTP for existing user |
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

## � Docker Compose

Two separate compose files for development and production:

| File | Use | Ports Exposed |
|------|-----|---------------|
| `docker-compose.dev.yml` | Local development | DB: 5432, Redis: 6379 |
| `docker-compose.yml` | Production | None (internal only) |

### Local Development

```bash
# Start services with exposed ports
make db       # Uses docker-compose.dev.yml
make run      # App runs on host, connects to localhost
```

### Production

```bash
# All services containerized, no ports exposed
docker compose up -d
docker compose exec app-api alembic upgrade head
```

---

## 📧 Email Configuration (OTP)

Email is required for OTP verification when users add passkeys to existing accounts.

### Gmail Setup

1. Enable 2-Step Verification at https://myaccount.google.com/security
2. Create an App Password at https://myaccount.google.com/apppasswords
3. Add to `.env`:

```bash
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=abcdefghijklmnop  # App Password (no spaces)
MAIL_FROM=your-email@gmail.com
MAIL_FROM_NAME="Your App Name"
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
```

---

## 🚀 Production Deployment

### Required Configuration

```bash
# Security
SECRET_KEY=your-secure-random-key  # openssl rand -hex 32
COOKIE_SECURE=true

# WebAuthn (cannot change after users register!)
WEBAUTHN_RP_ID=yourdomain.com
WEBAUTHN_RP_NAME=Your App Name
WEBAUTHN_ORIGIN=https://yourdomain.com

# Database (use Docker service name)
POSTGRES_SERVER=db

# Email
MAIL_USERNAME=noreply@yourdomain.com
MAIL_FROM=noreply@yourdomain.com
```

### ⚠️ Important Notes

1. **WEBAUTHN_RP_ID cannot change** after users create passkeys
2. **HTTPS is required** for passkeys in production
3. **COOKIE_SECURE=true** is mandatory for HTTPS

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
│   │   ├── otp.py               # OTP generation/verification
│   │   └── email.py             # Email service
│   └── main.py                  # FastAPI app
├── alembic/                     # Database migrations
├── tests/                       # Test suite
├── docker-compose.yml           # Production
├── docker-compose.dev.yml       # Development
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
| `MAIL_USERNAME` | SMTP username | - |
| `MAIL_PASSWORD` | SMTP password/app password | - |
| `MAIL_FROM` | Sender email address | `noreply@example.com` |
| `MAIL_SERVER` | SMTP server | `smtp.gmail.com` |
| `OTP_EXPIRE_MINUTES` | OTP validity | `10` |
| `OTP_MAX_ATTEMPTS` | Max OTP verification attempts | `3` |
| `RATE_LIMIT_REQUESTS` | Max requests per window | `100` |

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

const email = 'user@example.com';

// 1. Start registration
const beginRes = await fetch('/api/v1/passkeys/register/begin', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email })
}).then(r => r.json());

// 2. Check if OTP is required (existing user)
if (beginRes.requires_otp) {
  // User enters OTP from email, then verify
  const verifyRes = await fetch('/api/v1/passkeys/register/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp: '123456' })
  }).then(r => r.json());
  beginRes.options = verifyRes.options;
}

// 3. Create passkey (browser handles biometrics)
const credential = await startRegistration({ optionsJSON: beginRes.options });

// 4. Complete registration
await fetch('/api/v1/passkeys/register/complete', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({ email, credential })
});
```

---

## License

MIT
