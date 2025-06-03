from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest import Guest as GuestModel
from app.schemas.guest import GuestCreate, GuestInDB, GuestUpdate

class GuestService:
    """Service for handling guest operations"""
    
    async def create_guest(
        self,
        guest_in: GuestCreate,
        created_by: str,
        organization_id: str,
        db: AsyncSession
    ) -> GuestInDB:
        """
        Create a new guest
        """
        # Check if guest with same email already exists in organization
        existing_guest = await self._get_guest_by_email(guest_in.email, organization_id, db)
        if existing_guest:
            # Update existing guest if found
            return await self.update_guest(
                guest_id=str(existing_guest.id),
                guest_in=GuestUpdate(**guest_in.dict()),
                db=db
            )
        
        # Create new guest
        guest_data = guest_in.dict()
        guest_data['created_by'] = created_by
        guest_data['organization_id'] = organization_id
        
        db_guest = GuestModel(**guest_data)
        db.add(db_guest)
        await db.commit()
        await db.refresh(db_guest)
        
        return db_guest
    
    async def get_guest(
        self,
        guest_id: str,
        db: AsyncSession
    ) -> Optional[GuestInDB]:
        """
        Get a guest by ID
        """
        result = await db.execute(
            select(GuestModel).where(GuestModel.id == guest_id)
        )
        return result.scalars().first()
    
    async def _get_guest_by_email(
        self,
        email: str,
        organization_id: str,
        db: AsyncSession
    ) -> Optional[GuestInDB]:
        """
        Get a guest by email within an organization
        """
        result = await db.execute(
            select(GuestModel)
            .where(
                GuestModel.email == email.lower(),
                GuestModel.organization_id == organization_id
            )
        )
        return result.scalars().first()
    
    async def list_guests(
        self,
        organization_id: str,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        db: AsyncSession = None
    ) -> List[GuestInDB]:
        """
        List guests with optional search
        """
        query = select(GuestModel).where(GuestModel.organization_id == organization_id)
        
        if search:
            search = f"%{search}%"
            query = query.where(
                or_(
                    GuestModel.first_name.ilike(search),
                    GuestModel.last_name.ilike(search),
                    GuestModel.email.ilike(search),
                    GuestModel.phone.ilike(search)
                )
            )
        
        result = await db.execute(
            query.order_by(GuestModel.last_name, GuestModel.first_name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update_guest(
        self,
        guest_id: str,
        guest_in: GuestUpdate,
        db: AsyncSession
    ) -> GuestInDB:
        """
        Update a guest
        """
        guest = await self.get_guest(guest_id, db)
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest not found"
            )
        
        # Check if email is being updated to an existing one
        if guest_in.email and guest_in.email.lower() != guest.email.lower():
            existing_guest = await self._get_guest_by_email(
                guest_in.email, 
                guest.organization_id, 
                db
            )
            if existing_guest and str(existing_guest.id) != guest_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use by another guest"
                )
        
        # Update fields
        update_data = guest_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(guest, field, value)
        
        guest.updated_at = datetime.utcnow()
        
        db.add(guest)
        await db.commit()
        await db.refresh(guest)
        
        return guest
    
    async def delete_guest(
        self,
        guest_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Delete a guest
        """
        guest = await self.get_guest(guest_id, db)
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest not found"
            )
        
        # Soft delete by setting deleted_at
        guest.deleted_at = datetime.utcnow()
        
        db.add(guest)
        await db.commit()
        
        return True

# Singleton instance
guest_service = GuestService()

def get_guest_service() -> GuestService:
    return guest_service
