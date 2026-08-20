# Security API - Backend

REST API with API Key authentication (Security Anti-Pattern Demonstration)

## Requirements

- Python 3.8+
- pip
- Windows 10/11, Mac, or Linux

## Installation

### 1. Clone the repository
git clone https://github.com/eri-1485l/security-api.git
cd security-api 


### 2. Create virtual environment
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

### 3. Install dependencies
pip install -r requirements.txt

## Running the Server
python main.py
The server will run at http://localhost:8000

## Documentation
Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

## API Key
mi-api-key-secreta-123456

## Testing
# Health (public)
curl http://localhost:8000/health

# GET protected (requires API Key)
curl -H "x-api-key: mi-api-key-secreta-123456" http://localhost:8000/api/data

# POST protected
curl -X POST -H "x-api-key: mi-api-key-secreta-123456" -H "Content-Type: application/json" -d '{"nombre":"Test"}' http://localhost:8000/api/data

# Technologies Used
FastAPI: Modern Python web framework
Uvicorn: ASGI server
Python 3.11.9: Programming language