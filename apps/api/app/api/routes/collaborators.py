"""API Route: Collaborators"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/collaborators", tags=["collaborators"])

@router.get("/")
def get_collaborators_root():
    return {"status": "ok", "resource": "collaborators"}
