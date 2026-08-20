from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uvicorn

# ============================================
# CONFIGURATION
# ============================================

app = FastAPI(
    title="Security API",
    description="Demo API with API Key authentication (security anti-pattern)",
    version="1.0.0"
)

# CORS configuration to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key configuration
API_KEY = "mi-api-key-secreta-123456"

# ============================================
# DATA MODELS
# ============================================

class DataRequest(BaseModel):
    """Model for POST request input data"""
    nombre: Optional[str] = None
    mensaje: Optional[str] = None
    timestamp: Optional[str] = None

class DataResponse(BaseModel):
    """Model for GET response data"""
    message: str
    course: str
    status: str
    data: dict

class HealthResponse(BaseModel):
    """Model for health check response"""
    status: str
    timestamp: str

# ============================================
# AUTHENTICATION FUNCTIONS
# ============================================

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Verifies that the API Key is valid.
    This function is used as a dependency in protected endpoints.
    """
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required. Send 'x-api-key' header"
        )
    
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    
    return x_api_key

# ============================================
# ENDPOINTS
# ============================================

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Check server status",
    description="Public endpoint that does not require authentication"
)
async def health_check():
    """
    Server health endpoint.
    No API Key required.
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat()
    )


@app.get(
    "/api/data",
    response_model=DataResponse,
    summary="Get protected data",
    description="Returns static data. Requires API Key authentication."
)
async def get_protected_data(api_key: Optional[str] = Header(None, alias="x-api-key")):
    """
    Gets protected data.
    Requires 'x-api-key' header with the correct key.
    """
    # Verify API Key
    verify_api_key(api_key)
    
    # Return protected data
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


@app.post(
    "/api/data",
    summary="Send protected data",
    description="Protected endpoint that accepts data. Requires API Key."
)
async def post_protected_data(
    request_data: Optional[DataRequest] = None,
    api_key: Optional[str] = Header(None, alias="x-api-key")
):
    """
    Receives data in the body.
    Requires 'x-api-key' header with the correct key.
    """
    # Verify API Key
    verify_api_key(api_key)
    
    # Return confirmation
    return {
        "message": "POST received",
        "receivedData": request_data.dict() if request_data else {},
        "timestamp": datetime.now().isoformat()
    }

# ============================================
# CUSTOM ERROR HANDLING
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Customizes error message for 401"""
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
    print("SERVER STARTED")
    print("="*60)
    print(f"API URL: http://localhost:8000")
    print(f" Documentation: http://localhost:8000/docs")
    print(f" API Key: {API_KEY}")
    print("="*60)
    print("\n Available endpoints:")
    print("   GET  /health     (Public) ")
    print("   GET  /api/data   (Protected) ")
    print("   POST /api/data   (Protected) ")
    print("\n" + "="*60)
    print("Press CTRL+C to stop the server\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)