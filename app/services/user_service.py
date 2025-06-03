from typing import Any, Dict, List, Optional, Union

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash, verify_password
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserUpdate

class UserService:
    """Service for user operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get(self, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id)
        )
        return result.scalars().first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.email == email)
        )
        return result.scalars().first()
    
    async def get_multi(
        self, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[User]:
        """Get multiple users with optional filtering"""
        query = select(User).options(
            selectinload(User.roles).selectinload(Role.permissions)
        ).offset(skip).limit(limit)
        
        if filters:
            conditions = []
            if "email" in filters and filters["email"]:
                conditions.append(User.email.ilike(f"%{filters['email']}%"))
            if "full_name" in filters and filters["full_name"]:
                conditions.append(User.full_name.ilike(f"%{filters['full_name']}%"))
            if "is_active" in filters and filters["is_active"] is not None:
                conditions.append(User.is_active == filters["is_active"])
            if "role_id" in filters and filters["role_id"]:
                conditions.append(User.roles.any(id=filters["role_id"]))
                
            if conditions:
                query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(self, user_in: Union[UserCreate, Dict[str, Any]]) -> User:
        """Create a new user"""
        if isinstance(user_in, dict):
            user_data = user_in.copy()
        else:
            user_data = user_in.dict(exclude_unset=True)
        
        # Hash password
        if "password" in user_data:
            hashed_password = get_password_hash(user_data["password"])
            user_data["hashed_password"] = hashed_password
            del user_data["password"]
        
        # Create user
        db_user = User(**user_data)
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user
    
    async def update(
        self, 
        db_user: User, 
        user_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """Update a user"""
        if isinstance(user_in, dict):
            update_data = user_in
        else:
            update_data = user_in.dict(exclude_unset=True)
        
        # Handle password update
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            update_data["hashed_password"] = hashed_password
            del update_data["password"]
        
        # Update user data
        for field, value in update_data.items():
            if field != "roles" and hasattr(db_user, field):
                setattr(db_user, field, value)
        
        # Update roles if provided
        if "role_ids" in update_data:
            await self._update_user_roles(db_user, update_data["role_ids"])
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user
    
    async def delete(self, user_id: int) -> bool:
        """Delete a user"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        db_user = result.scalars().first()
        
        if db_user:
            await self.db.delete(db_user)
            await self.db.commit()
            return True
        return False
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user"""
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def _update_user_roles(self, user: User, role_ids: List[int]) -> None:
        """Update user roles"""
        # Get existing roles
        result = await self.db.execute(
            select(Role).where(Role.id.in_(role_ids))
        )
        roles = result.scalars().all()
        
        # Update user roles
        user.roles = roles
        self.db.add(user)
        await self.db.commit()
    
    async def add_role(self, user_id: int, role_id: int) -> bool:
        """Add a role to a user"""
        user = await self.get(user_id)
        if not user:
            return False
            
        result = await self.db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalars().first()
        
        if not role:
            return False
        
        if role not in user.roles:
            user.roles.append(role)
            self.db.add(user)
            await self.db.commit()
            
        return True
    
    async def remove_role(self, user_id: int, role_id: int) -> bool:
        """Remove a role from a user"""
        user = await self.get(user_id)
        if not user:
            return False
            
        role = next((r for r in user.roles if r.id == role_id), None)
        if role:
            user.roles.remove(role)
            self.db.add(user)
            await self.db.commit()
            return True
            
        return False
