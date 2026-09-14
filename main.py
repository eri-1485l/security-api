from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables initially
load_dotenv()

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable is required")

from services.crypto_service import CryptoService
from services.ldap_service import LDAPService

app = FastAPI(
    title="Security API",
    description="Demo API with API Key authentication, encryption, and LDAP login",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

crypto_service = CryptoService()
ldap_service = LDAPService()


# ============================================
# DATA MODELS
# ============================================

class DataRequest(BaseModel):
    nombre: Optional[str] = None
    mensaje: Optional[str] = None
    timestamp: Optional[str] = None


class DataResponse(BaseModel):
    message: str
    course: str
    status: str
    data: dict


class HealthResponse(BaseModel):
    status: str
    timestamp: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    authenticated: bool
    username: str
    dn: str


# ============================================
# AUTHENTICATION
# ============================================

def get_api_key() -> str:
    """
    Reads the API_KEY from the .env file on each request.
    This allows the key to be rotated without restarting the server.
    """
    load_dotenv(override=True)
    return os.getenv("API_KEY")


def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Verifies the API Key by reading the current value from the .env file.
    """
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required. Send 'x-api-key' header"
        )

    current_api_key = get_api_key()

    if x_api_key != current_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

    return x_api_key


# ============================================
# ENDPOINTS
# ============================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat()
    )


@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate a user against LDAP.
    """
    if ldap_service.authenticate(request.username, request.password):
        return LoginResponse(
            authenticated=True,
            username=request.username,
            dn=ldap_service.get_user_dn(request.username)
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )


@app.get("/api/data", response_model=DataResponse)
async def get_protected_data(api_key: Optional[str] = Header(None, alias="x-api-key")):
    verify_api_key(api_key)

    return DataResponse(
        message="Protected data",
        course="Security Exercise",
        status="success",
        data={
            "id": 1,
            "name": "Example protected data",
            "description": "This is an example of data that requires authentication",
            "createdAt": datetime.now().isoformat()
        }
    )


@app.post("/api/data")
async def post_protected_data(
    request_data: Optional[DataRequest] = None,
    api_key: Optional[str] = Header(None, alias="x-api-key")
):
    verify_api_key(api_key)

    return {
        "message": "POST received",
        "receivedData": request_data.dict() if request_data else {},
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/encrypt")
async def encrypt_data(
    request_data: DataRequest,
    api_key: Optional[str] = Header(None, alias="x-api-key")
):
    verify_api_key(api_key)

    if not request_data.mensaje:
        raise HTTPException(status_code=400, detail="The 'mensaje' field is required")

    try:
        encrypted = crypto_service.encrypt(request_data.mensaje)
        return {
            "message": "Data encrypted successfully",
            "encrypted_data": encrypted,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption error: {str(e)}")


@app.post("/api/decrypt")
async def decrypt_data(
    request_data: DataRequest,
    api_key: Optional[str] = Header(None, alias="x-api-key")
):
    verify_api_key(api_key)

    if not request_data.mensaje:
        raise HTTPException(status_code=400, detail="The 'mensaje' field is required")

    try:
        decrypted = crypto_service.decrypt(request_data.mensaje)
        return {
            "message": "Data decrypted successfully",
            "plaintext": decrypted,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption error: {str(e)}")


# ============================================
# ERROR HANDLING
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 401:
        return JSONResponse(
            status_code=401,
            content={
                "error": "Unauthorized",
                "detail": exc.detail,
                "message": "Please provide a valid API Key in the 'x-api-key' header"
            }
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


# ============================================
# SERVER STARTUP
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SECURITY API STARTED")
    print("="*60)
    print(f"API URL: http://localhost:8000")
    print(f"Documentation: http://localhost:8000/docs")
    print(f"API Key: {API_KEY}")
    print(f"Encryption Key: {os.getenv('DATABASE_ENCRYPTION_KEY', 'NOT SET')[:10]}...")
    print(f"LDAP Server: {os.getenv('LDAP_SERVER', 'NOT SET')}")
    print("="*60)
    print("\nAvailable endpoints:")
    print("   GET  /health          (Public)")
    print("   POST /login           (LDAP Authentication - NEW)")
    print("   GET  /api/data        (Protected)")
    print("   POST /api/data        (Protected)")
    print("   POST /api/encrypt     (Protected)")
    print("   POST /api/decrypt     (Protected)")
    print("\n" + "="*60)
    print("Press CTRL+C to stop the server\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
