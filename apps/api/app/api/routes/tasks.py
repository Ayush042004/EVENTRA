"""API Route: Tasks"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/")
def get_tasks_root():
    return {"status": "ok", "resource": "tasks"}
