from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_active_user
from app.schemas.checkout import CheckoutSessionCreate, CheckoutSessionInDB
from app.api.v1.services.checkout_service import CheckoutService

router = APIRouter()

@router.post("/create-session", response_model=Dict[str, Any])
async def create_checkout_session(
    checkout_data: CheckoutSessionCreate,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Create a new checkout session
    """
    checkout_service = CheckoutService()
    try:
        session = await checkout_service.create_session(
            user_id=current_user.id,
            items=checkout_data.items,
            success_url=checkout_data.success_url,
            cancel_url=checkout_data.cancel_url,
        )
        return {"session_id": session.id, "url": session.url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/sessions", response_model=List[CheckoutSessionInDB])
async def get_user_checkout_sessions(
    skip: int = 0,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get checkout sessions for the current user
    """
    checkout_service = CheckoutService()
    return await checkout_service.get_user_sessions(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

@router.get("/session/{session_id}", response_model=CheckoutSessionInDB)
async def get_checkout_session(
    session_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
) -> Any:
    """
    Get a specific checkout session by ID
    """
    checkout_service = CheckoutService()
    session = await checkout_service.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Checkout session not found"
        )
    
    # Ensure the user can only access their own sessions
    if str(session.user_id) != str(current_user.id) and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    return session
