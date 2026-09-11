# Security API - Backend

REST API with API Key authentication and AES-GCM encryption/decryption (Security Anti-Pattern Demonstration).

Protected endpoints require the `x-api-key` header. Encryption uses a 256-bit key loaded from the environment (`DATABASE_ENCRYPTION_KEY`). Secrets are no longer hardcoded in `main.py`; they are loaded from a `.env` file with `python-dotenv`.

## Requirements

- Python 3.8+
- pip
- Docker (needed if you run the frontend container or `rotate_secret.py`)
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

This installs FastAPI, Uvicorn, `python-dotenv`, `cryptography`, and related packages.

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

The application loads variables from `.env` using `python-dotenv`. `API_KEY` and `DATABASE_ENCRYPTION_KEY` are both required.

| Variable | Purpose | Rotates? |
| -------- | ------- | -------- |
| `API_KEY` | Authentication for protected endpoints (`x-api-key` header) | Yes — every 2 minutes via `rotate_secret.py` |
| `DATABASE_ENCRYPTION_KEY` | 32-byte AES-GCM key (Base64) used by `CryptoService` | **No** — must stay stable so ciphertext remains readable |

Example `.env`:

```bash
API_KEY=replace-with-a-lab-only-key
DATABASE_ENCRYPTION_KEY=replace-with-a-32-byte-base64-key
```

### Generate a valid `DATABASE_ENCRYPTION_KEY`

The key must decode to **exactly 32 bytes**. Generate a URL-safe Base64 value:

```python
python -c "import os, base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
```

Paste the output into `.env` as `DATABASE_ENCRYPTION_KEY`.

## File structure (relevant)

- `main.py` — FastAPI app, auth, encrypt/decrypt routes
- `services/crypto_service.py` — `CryptoService` with `encrypt()` and `decrypt()` (AES-GCM, 256-bit)
- `.env` — `API_KEY` and `DATABASE_ENCRYPTION_KEY`
- `rotate_secret.py` — rotates `API_KEY` and updates the frontend container

## Testing

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

`rotate_secret.py` rotates **only** `API_KEY`. It does **not** rotate `DATABASE_ENCRYPTION_KEY`, so existing encrypted data stays decryptable.

From the `security-api` folder (with the virtual environment activated and Docker available for the frontend):

```bash
python rotate_secret.py
```

What it does:

1. Waits 2 minutes, then generates a new `API_KEY` (or rotate immediately with **Ctrl+C** during the first wait)
2. Writes the new key into `.env`
3. Restarts the `security-frontend` container with the new `API_KEY` so Nginx injects the updated header
4. Leaves `DATABASE_ENCRYPTION_KEY` unchanged
5. Continues rotating `API_KEY` every 2 minutes until you stop the script

After a rotation, restart the API (`python main.py`) so it reloads `API_KEY` from `.env`.

### Validate the rotation

Windows:

```bash
type .env | findstr API_KEY
```

Linux / Mac:

```bash
cat .env | grep API_KEY
```

Confirm `DATABASE_ENCRYPTION_KEY` is unchanged:

```bash
# Windows
type .env | findstr DATABASE_ENCRYPTION_KEY

# Linux / Mac
cat .env | grep DATABASE_ENCRYPTION_KEY
```

## Security notes

- Never commit real secrets to the repository. Keep `.env` out of Git.
- Use lab-only values for `API_KEY` and `DATABASE_ENCRYPTION_KEY`.
- Do not rotate `DATABASE_ENCRYPTION_KEY` without a migration that re-encrypts stored data. Changing it makes existing ciphertext unreadable.

## Technologies Used

- FastAPI: Modern Python web framework
- Uvicorn: ASGI server
- python-dotenv: Load secrets from `.env`
- cryptography: AES-GCM encryption
- Python 3.11.9: Programming language
