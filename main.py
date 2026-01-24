import os
import json
import hashlib
import re
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

# --- INTEGRACIÓN DE MÓDULOS ---
from utils import normalize_address, is_valid_alias
from agent import parse_payment_command
from blockchain_service import BlockchainService
from circle_service import CircleService

# ============================================================================
# CONFIGURATION & SECURITY HARDENING
# ============================================================================
class Config:
    API_VERSION = "v1"
    APP_NAME = "Bulut API"
    ENVIRONMENT = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT") or 8000)
    
    AI_AGENT_API_KEY = os.getenv("AIMLAPI_KEY", "")
    ARC_RPC_URL = os.getenv("ARC_RPC_URL", "https://mainnet.arc.network")
    ARC_CHAIN_ID = int(os.getenv("ARC_CHAIN_ID", "4224"))
    ARC_USDC_ADDRESS = os.getenv("ARC_USDC_ADDRESS", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    
    CIRCLE_API_KEY = os.getenv("CIRCLE_API_KEY", "")
    CIRCLE_BASE_URL = os.getenv("CIRCLE_BASE_URL", "https://api.circle.com/v1/w3s")
    CIRCLE_ENTITY_ID = os.getenv("CIRCLE_ENTITY_ID", "")
    
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    def __init__(self):
        # Bloqueo de seguridad para producción
        if self.ENVIRONMENT == "production":
            if self.JWT_SECRET == "dev-secret-change-in-production":
                raise RuntimeError("CRITICAL: JWT_SECRET must be changed in production mode.")
            if not self.AI_AGENT_API_KEY:
                raise RuntimeError("CRITICAL: AIMLAPI_KEY is required for production.")
            self.DEBUG = False

config = Config()

# Configuración de Logging Estructurado
logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bulut-api")

# ============================================================================
# DATA MODELS
# ============================================================================
