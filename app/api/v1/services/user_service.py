from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import random
from bson import ObjectId

from app.core.security import get_password_hash, verify_password
from app.database.connection import get_database
from app.models.user import UserCreate, UserUpdate, UserInDB, UserRole
from app.core.config import settings

class UserService:
    """Service class for user operations."""
    
    def __init__(self):
        self.db = get_database()
        self.users_collection = self.db.users

    async def create_user(self, user_create: UserCreate) -> UserInDB:
        """
        Create a new user.
        """
        # Check if user with this email already exists
        existing_user = await self.users_collection.find_one({"email": user_create.email})
        if existing_user:
            raise ValueError("User with this email already exists")
            
        # Check password confirmation
        if user_create.password != user_create.passwordConfirm:
            raise ValueError("Passwords do not match")
            
        # Create user document
        user_dict = user_create.model_dump(exclude={"passwordConfirm"})
        user_dict["hashed_password"] = get_password_hash(user_create.password)
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        
        # Set default role for first user
        if await self.users_collection.count_documents({}) == 0:
            user_dict["role"] = UserRole.ADMIN
            user_dict["approved"] = True
        
        # Insert user
        result = await self.users_collection.insert_one(user_dict)
        user = await self.users_collection.find_one({"_id": result.inserted_id})
        return UserInDB(**user)

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """
        Get user by ID.
        """
        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        return UserInDB(**user) if user else None

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Get user by email.
        """
        user = await self.users_collection.find_one({"email": email})
        return UserInDB(**user) if user else None

    async def update_user(
        self, 
        user_id: str, 
        user_update: UserUpdate,
        current_user: UserInDB
    ) -> UserInDB:
        """
        Update user information.
        """
        # Check if user exists
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
            
        # Only admins can update other users
        if current_user.role != UserRole.ADMIN and str(current_user.id) != user_id:
            raise ValueError("Not enough permissions")
            
        # Only admins can change roles
        if user_update.role and current_user.role != UserRole.ADMIN:
            raise ValueError("Not enough permissions to change user role")
            
        # Update user
        update_data = user_update.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        # Get updated user
        updated_user = await self.get_user_by_id(user_id)
        if not updated_user:
            raise ValueError("User not found after update")
        return updated_user

    async def delete_user(self, user_id: str) -> None:
        """
        Delete a user.
        """
        await self.users_collection.delete_one({"_id": ObjectId(user_id)})

    async def authenticate(self, email: str, password: str) -> Optional[UserInDB]:
        """
        Authenticate a user with email and password.
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
            
        if not verify_password(password, user.hashed_password):
            return None
            
        # Check if user is active
        if not user.is_active:
            raise ValueError("User account is disabled")
            
        return user
        
    async def generate_otp(self, user_id: str, expires_minutes: int = 15) -> Tuple[str, datetime]:
        """
        Generate and store an OTP for password reset.
        Returns the OTP and its expiration time.
        """
        # Generate a 6-digit OTP
        otp = str(random.randint(100000, 999999))
        otp_expires = datetime.utcnow() + timedelta(minutes=expires_minutes)
        
        # Store OTP in user document
        await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"otp": otp, "otp_expires": otp_expires}}
        )
        
        return otp, otp_expires
        
    async def verify_otp(self, user_id: str, otp: str) -> bool:
        """
        Verify if the provided OTP is valid for the user.
        """
        user = await self.users_collection.find_one({
            "_id": ObjectId(user_id),
            "otp": otp,
            "otp_expires": {"$gt": datetime.utcnow()}
        })
        
        return user is not None
    
    async def reset_password_with_otp(self, user_id: str, otp: str, new_password: str) -> bool:
        """
        Reset user's password using a valid OTP.
        """
        # Verify OTP first
        if not await self.verify_otp(user_id, otp):
            return False
            
        # Update password and clear OTP
        hashed_password = get_password_hash(new_password)
        result = await self.users_collection.update_one(
            {"_id": ObjectId(user_id), "otp": otp},
            {"$set": {"hashed_password": hashed_password}, 
             "$unset": {"otp": "", "otp_expires": ""}}
        )
        
        return result.modified_count > 0
        
    async def update_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Update user's password by providing the current password.
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
            
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
            
        hashed_password = get_password_hash(new_password)
        result = await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"hashed_password": hashed_password, "updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
        
    async def initiate_password_reset(self, email: str) -> Optional[Tuple[str, str]]:
        """
        Initiate password reset by generating and returning an OTP.
        Returns a tuple of (user_id, otp) if successful, None otherwise.
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
            
        otp, _ = await self.generate_otp(str(user.id))
        return str(user.id), otp
        
    async def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account.
        """
        result = await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
        
    async def activate_user(self, user_id: str) -> bool:
        """
        Activate a user account.
        """
        result = await self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": True, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserInDB]:
        """
        Get list of users.
        """
        users = await self.users_collection.find().skip(skip).limit(limit).to_list(100)
        return [UserInDB(**user) for user in users]

    async def get_not_attended_users(self, event_id: str) -> List[UserInDB]:
        """
        Get users who did not attend a specific event.
        """
        # Get users who attended the event
        attended_users = await self.db.attendances.find({
            "eventId": ObjectId(event_id)
        }).distinct("userId")
        
        # Get all users who are not in the attended list
        users = await self.users_collection.find({
            "_id": {"$nin": attended_users}
        }).to_list(100)
        
        return [UserInDB(**user) for user in users]