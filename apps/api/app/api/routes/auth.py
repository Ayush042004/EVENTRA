"""API Route: Auth"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/")
def get_auth_root():
    return {"status": "ok", "resource": "auth"}
