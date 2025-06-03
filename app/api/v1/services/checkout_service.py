from typing import Any, Dict, List, Optional
import stripe
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.checkout import CheckoutSession
from app.schemas.checkout import CheckoutItem, CheckoutSessionCreate, CheckoutSessionInDB

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class CheckoutService:
    """Service for handling checkout operations"""
    
    async def create_session(
        self,
        user_id: str,
        items: List[CheckoutItem],
        success_url: str,
        cancel_url: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Create a new checkout session
        """
        try:
            # Create line items for Stripe
            line_items = []
            for item in items:
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': item.name,
                            'description': item.description,
                        },
                        'unit_amount': int(item.price * 100),  # Convert to cents
                    },
                    'quantity': item.quantity,
                })
            
            # Create Stripe checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=user_id,
            )
            
            # Save session to database
            db_session = CheckoutSession(
                id=session.id,
                user_id=user_id,
                status=session.payment_status,
                amount_total=session.amount_total / 100,  # Convert from cents
                payment_intent=session.payment_intent,
                payment_status=session.payment_status,
                url=session.url,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'items': [item.dict() for item in items]
                }
            )
            
            db.add(db_session)
            await db.commit()
            await db.refresh(db_session)
            
            return {
                'id': session.id,
                'url': session.url,
                'amount_total': session.amount_total / 100,
                'payment_status': session.payment_status,
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    async def get_session(
        self, 
        session_id: str,
        db: AsyncSession
    ) -> Optional[CheckoutSessionInDB]:
        """
        Get a checkout session by ID
        """
        try:
            # Get from database
            result = await db.execute(
                select(CheckoutSession).where(CheckoutSession.id == session_id)
            )
            db_session = result.scalars().first()
            
            if not db_session:
                return None
                
            # Update from Stripe if needed
            if db_session.payment_status not in ['paid', 'complete']:
                try:
                    stripe_session = stripe.checkout.Session.retrieve(session_id)
                    
                    # Update local session if status changed
                    if stripe_session.payment_status != db_session.payment_status:
                        db_session.status = stripe_session.payment_status
                        db_session.payment_status = stripe_session.payment_status
                        
                        if stripe_session.payment_status == 'paid':
                            db_session.paid_at = datetime.utcnow()
                        
                        await db.commit()
                        await db.refresh(db_session)
                except stripe.error.StripeError:
                    pass  # Use local data if Stripe fetch fails
            
            return db_session
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    async def get_user_sessions(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = None
    ) -> List[CheckoutSessionInDB]:
        """
        Get all checkout sessions for a user
        """
        result = await db.execute(
            select(CheckoutSession)
            .where(CheckoutSession.user_id == user_id)
            .order_by(CheckoutSession.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

# Singleton instance
checkout_service = CheckoutService()

def get_checkout_service() -> CheckoutService:
    return checkout_service
