# Security API - Backend

REST API with API Key authentication, AES-GCM encryption/decryption, and LDAP authentication (Security Anti-Pattern Demonstration).

Protected endpoints require the `x-api-key` header. Encryption uses a 256-bit key loaded from the environment (`DATABASE_ENCRYPTION_KEY`). User login is validated against LDAP via `POST /login`. Secrets are loaded from a `.env` file with `python-dotenv`.

The backend reads `API_KEY` from `.env` on **each request**, so the server does not need to be restarted when the key is rotated.

## Prerequisites

- Python 3.8+
- pip
- Docker (needed to run OpenLDAP and the frontend container)
- An LDAP server available at `ldap://localhost:389` (for example the OpenLDAP container from the LDAP lab)
- Windows 10/11, Mac, or Linux

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/eri-1485l/security-api.git
cd security-api
```

### 2. Create virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, `python-dotenv`, `cryptography`, `python-ldap`, and related packages.

### 4. Configure environment variables

Create a `.env` file in the project root (do not commit real secrets). See [Environment variables](#environment-variables).

## Running the Server

```bash
python main.py
```

The server will run at http://localhost:8000

## Documentation

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

## Environment variables

The application loads variables from `.env` using `python-dotenv`. `API_KEY` and `DATABASE_ENCRYPTION_KEY` are both required. LDAP settings are used by `LDAPService`.

| Variable | Purpose | Rotates? |
| -------- | ------- | -------- |
| `API_KEY` | Authentication for protected endpoints (`x-api-key` header) | Yes — every 2 minutes via `rotate-secrets` |
| `DATABASE_ENCRYPTION_KEY` | 32-byte AES-GCM key (Base64) used by `CryptoService` | **No** — must stay stable so ciphertext remains readable |
| `LDAP_SERVER` | LDAP URL used by `LDAPService` | No |
| `LDAP_BASE_DN` | Base DN for user lookups | No |
| `LDAP_ADMIN_DN` | LDAP admin bind DN | No |
| `LDAP_ADMIN_PASSWORD` | LDAP admin password | Yes — every 2 minutes via `rotate-secrets` |

Example `.env`:

```bash
API_KEY=replace-with-a-lab-only-key
DATABASE_ENCRYPTION_KEY=replace-with-a-32-byte-base64-key
LDAP_SERVER=ldap://localhost:389
LDAP_BASE_DN=dc=example,dc=com
LDAP_ADMIN_DN=cn=admin,dc=example,dc=com
LDAP_ADMIN_PASSWORD=adminpassword
```

### Generate a valid `DATABASE_ENCRYPTION_KEY`

The key must decode to **exactly 32 bytes**. Generate a URL-safe Base64 value:

```python
python -c "import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

Paste the output into `.env` as `DATABASE_ENCRYPTION_KEY`.

## File structure (relevant)

- `main.py` — FastAPI app, auth, LDAP login, encrypt/decrypt routes
- `services/crypto_service.py` — `CryptoService` with `encrypt()` and `decrypt()` (AES-GCM, 256-bit)
- `services/ldap_service.py` — `LDAPService` with `authenticate()` and `get_user_dn()`
- `.env` — `API_KEY`, `DATABASE_ENCRYPTION_KEY`, and LDAP settings

Secret rotation lives in a separate repository (`rotate-secrets`). It updates `.env` and recreates the frontend container. The API does not need a restart after `API_KEY` rotation because the key is re-read from `.env` on every request.

## Endpoints

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| `GET` | `/health` | Public | Health check |
| `POST` | `/login` | LDAP credentials | Authenticate a user against LDAP |
| `GET` | `/api/data` | `x-api-key` | Protected data |
| `POST` | `/api/data` | `x-api-key` | Protected POST |
| `POST` | `/api/encrypt` | `x-api-key` | Encrypt a message (AES-GCM) |
| `POST` | `/api/decrypt` | `x-api-key` | Decrypt a message (AES-GCM) |

## Testing LDAP login

OpenLDAP must be running. Lab users such as `alice` / `alice123` come from the LDAP exercise.

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"alice\",\"password\":\"alice123\"}"
```

Success response (`200`):

```json
{
  "authenticated": true,
  "username": "alice",
  "dn": "uid=alice,ou=users,dc=example,dc=com"
}
```

Invalid credentials return `401`.

## Testing protected endpoints

Replace `YOUR_API_KEY` with the current value of `API_KEY` from `.env`.

```bash
# Health (public)
curl http://localhost:8000/health

# GET protected (requires API Key)
curl -H "x-api-key: YOUR_API_KEY" http://localhost:8000/api/data

# POST protected
curl -X POST -H "x-api-key: YOUR_API_KEY" -H "Content-Type: application/json" -d '{"nombre":"Test"}' http://localhost:8000/api/data
```

## Encryption endpoints

Both endpoints require the `x-api-key` header. The body field is `mensaje`. Encryption uses AES-GCM with a 256-bit key from `DATABASE_ENCRYPTION_KEY`. Ciphertext is Base64-encoded.

### `POST /api/encrypt`

Encrypts a plaintext message.

Request:

```bash
curl -X POST http://localhost:8000/api/encrypt \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"mensaje\":\"Hello world\"}"
```

```json
{
  "mensaje": "Hello world"
}
```

Response:

```json
{
  "message": "Data encrypted successfully",
  "encrypted_data": "base64-encoded-nonce-and-ciphertext",
  "timestamp": "2026-09-11T07:58:00"
}
```

### `POST /api/decrypt`

Decrypts a Base64-encoded AES-GCM payload (the `encrypted_data` value from encrypt).

Request:

```bash
curl -X POST http://localhost:8000/api/decrypt \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"mensaje\":\"PASTE_ENCRYPTED_DATA_HERE\"}"
```

```json
{
  "mensaje": "PASTE_ENCRYPTED_DATA_HERE"
}
```

Response:

```json
{
  "message": "Data decrypted successfully",
  "plaintext": "Hello world",
  "timestamp": "2026-09-11T07:58:00"
}
```

## Secret rotation

`API_KEY` and `LDAP_ADMIN_PASSWORD` are rotated by the separate `rotate-secrets` project (`rotate_secrets.py`). That script does **not** rotate `DATABASE_ENCRYPTION_KEY`, so existing encrypted data stays decryptable.

Because `get_api_key()` reloads `.env` on each request, you do **not** need to restart `python main.py` after an `API_KEY` rotation. The frontend container is recreated by the rotation script so Nginx injects the updated header.

## Security notes

- Never commit real secrets to the repository. Keep `.env` out of Git.
- Use lab-only values for `API_KEY`, `DATABASE_ENCRYPTION_KEY`, and LDAP credentials.
- Do not rotate `DATABASE_ENCRYPTION_KEY` without a migration that re-encrypts stored data. Changing it makes existing ciphertext unreadable.

## Technologies Used

- FastAPI: Modern Python web framework
- Uvicorn: ASGI server
- python-dotenv: Load secrets from `.env`
- cryptography: AES-GCM encryption
- python-ldap: LDAP bind and authentication
- Python 3.11.9: Programming language
