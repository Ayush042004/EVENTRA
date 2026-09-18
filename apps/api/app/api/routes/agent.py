"""API Endpoints: Event Operations Agent"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user_id, get_db_session
from app.schemas.agent import AgentRunRequest, AgentRunResponse
from app.agent.agent import EventOperationsAgent

router = APIRouter(prefix="/agent/events/{event_id}", tags=["Event Operations Agent"])


@router.post("/run", response_model=AgentRunResponse, status_code=status.HTTP_200_OK)
def run_agent_endpoint(
    event_id: str,
    payload: AgentRunRequest,
    db: Session = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user_id),
):
    """Executes the single Event Operations Agent loop for a live event."""
    agent = EventOperationsAgent(db)
    result = agent.run(
        event_id=event_id,
        message=payload.message,
        user_id=current_user_id,
        approval_id=payload.approval_id,
    )
    return result
