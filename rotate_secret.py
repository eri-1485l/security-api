#!/usr/bin/env python3
"""
Secret Rotation Script for Security API

This script:
1. Rotates API_KEY every 2 minutes (or manually with Ctrl+C)
2. Updates the .env file with the new key
3. Automatically restarts the frontend container with the new key
4. Preserves DATABASE_ENCRYPTION_KEY (does NOT rotate it)
"""

import os
import secrets
import time
import subprocess
import sys
from dotenv import load_dotenv, set_key

ENV_PATH = ".env"
ENV_KEY = "API_KEY"
FRONTEND_CONTAINER_NAME = "security-frontend"
FRONTEND_IMAGE_NAME = "security-frontend"
BACKEND_HOST = "host.docker.internal"
BACKEND_PORT = "8000"

def generate_new_key() -> str:
    return secrets.token_urlsafe(32)

def get_current_key() -> str:
    load_dotenv(ENV_PATH)
    return os.getenv(ENV_KEY, "NOT SET")

def update_env_file(new_key: str) -> None:
    load_dotenv(ENV_PATH)
    set_key(ENV_PATH, ENV_KEY, new_key)
    print("    .env updated with new key")

def get_encryption_key() -> str:
    load_dotenv(ENV_PATH)
    return os.getenv("DATABASE_ENCRYPTION_KEY", "NOT SET")

def update_frontend(new_key: str) -> bool:
    print("    Updating frontend...")
    
    try:
        subprocess.run(
            ["docker", "stop", FRONTEND_CONTAINER_NAME],
            check=False,
            capture_output=True
        )
        
        subprocess.run(
            ["docker", "rm", FRONTEND_CONTAINER_NAME],
            check=False,
            capture_output=True
        )
        
        subprocess.run([
            "docker", "run", "-d",
            "--name", FRONTEND_CONTAINER_NAME,
            "-p", "80:80",
            "-e", f"API_KEY={new_key}",
            "-e", f"BACKEND_HOST={BACKEND_HOST}",
            "-e", f"BACKEND_PORT={BACKEND_PORT}",
            "--add-host=host.docker.internal:host-gateway",
            FRONTEND_IMAGE_NAME
        ], check=True, capture_output=True, text=True)
        
        print("    Frontend updated successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"    Error updating frontend: {e.stderr}")
        return False
    except Exception as e:
        print(f"    Unexpected error: {e}")
        return False

def show_frontend_key():
    try:
        result = subprocess.run(
            ["docker", "exec", FRONTEND_CONTAINER_NAME, "env"],
            check=True,
            capture_output=True,
            text=True
        )
        for line in result.stdout.splitlines():
            if "API_KEY" in line:
                print(f"    Frontend API_KEY: {line}")
                break
    except Exception as e:
        print(f"    Could not read frontend key: {e}")

def rotate_key():
    print(f"\n[{time.strftime('%H:%M:%S')}] Rotating API_KEY...")
    
    new_key = generate_new_key()
    print(f"    New key generated: {new_key[:15]}...")
    
    old_key = get_current_key()
    print(f"    Previous key: {old_key[:15]}...")
    
    update_env_file(new_key)
    
    enc_key = get_encryption_key()
    print(f"    DATABASE_ENCRYPTION_KEY (unchanged): {enc_key[:15]}...")
    
    update_frontend(new_key)
    
    show_frontend_key()
    
    print(f"[{time.strftime('%H:%M:%S')}] Rotation completed")
    print("="*60)

def main():
    print("="*60)
    print("API_KEY ROTATION SERVICE")
    print("="*60)
    print("This script rotates the API_KEY every 2 minutes")
    print("Press Ctrl+C to rotate manually")
    print("="*60)
    
    current_key = get_current_key()
    print(f"\nCurrent backend key: {current_key[:20]}...")
    
    show_frontend_key()
    
    enc_key = get_encryption_key()
    print(f"DATABASE_ENCRYPTION_KEY: {enc_key[:20]}...")
    print("="*60)
    
    print("\nWaiting 2 minutes (120 seconds) for automatic rotation...")
    print("   Press Ctrl+C at any time to rotate manually")
    
    try:
        for i in range(120, 0, -10):
            print(f"\r   {i} seconds remaining... ", end="")
            time.sleep(10)
        print("\nAutomatic rotation triggered!")
    except KeyboardInterrupt:
        print("\nManual rotation triggered!")
    
    rotate_key()
    
    print("\n" + "="*60)
    print("Next rotation in 2 minutes")
    print("   Press Ctrl+C to exit or rotate manually")
    print("="*60)
    
    try:
        while True:
            time.sleep(120)
            rotate_key()
    except KeyboardInterrupt:
        print("\nRotation service stopped.")

if __name__ == "__main__":
    main()