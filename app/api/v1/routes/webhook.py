from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1.services.webhook_service import WebhookService

router = APIRouter()

@router.post("/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )
    
    webhook_service = WebhookService()
    try:
        event = webhook_service.construct_webhook_event(
            payload=payload,
            sig_header=sig_header,
            webhook_secret=settings.STRIPE_WEBHOOK_SECRET
        )
        
        # Process the event
        await webhook_service.handle_stripe_webhook(event)
        
        return {"status": "success"}
        
    except ValueError as e:
        # Invalid payload
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle other errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/sendgrid")
async def sendgrid_webhook(request: Request):
    """
    Handle SendGrid webhook events
    """
    try:
        payload = await request.json()
        webhook_service = WebhookService()
        await webhook_service.handle_sendgrid_webhook(payload)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/test")
async def test_webhook():
    """
    Test endpoint for webhook configuration
    """
    return {"status": "Webhook endpoint is working"}
