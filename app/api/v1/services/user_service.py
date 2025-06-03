from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta
import random
from bson import ObjectId
from pymongo.database import Database
from pymongo.collection import Collection

from app.core.security import get_password_hash, verify_password
from app.api.v1.models.user import UserCreate, UserUpdate, UserInDB, UserRole
from app.api.v1.models.attendance import AttendanceStatus # For get_not_attended_users
from app.core.config import settings
from app.core.logging import logger

class UserService:
    """Service class for user operations."""
    
    def __init__(self, db: Database):
        self.db: Database = db
        self.users_collection: Collection = self.db['users']
        self.attendance_collection: Collection = self.db['attendance'] # For get_not_attended_users

    def create_user(self, user_create: UserCreate) -> UserInDB:
        """Create a new user."""
        existing_user = self.users_collection.find_one({"email": user_create.email})
        if existing_user:
            logger.warning(f"Attempt to create user with existing email: {user_create.email}")
            raise ValueError("User with this email already exists")
            
        if user_create.password != user_create.passwordConfirm:
            raise ValueError("Passwords do not match")
            
        user_dict = user_create.model_dump(exclude={"passwordConfirm"})
        user_dict["hashed_password"] = get_password_hash(user_create.password)
        user_dict["created_at"] = datetime.utcnow()
        user_dict["updated_at"] = datetime.utcnow()
        user_dict["is_active"] = user_dict.get("is_active", True) # Default to active
        user_dict["approved"] = user_dict.get("approved", False) # Default to not approved
        user_dict["role"] = user_dict.get("role", UserRole.USER).value # Default role

        if self.users_collection.count_documents({}) == 0:
            logger.info("First user created, assigning ADMIN role and approving.")
            user_dict["role"] = UserRole.ADMIN.value
            user_dict["approved"] = True
        
        result = self.users_collection.insert_one(user_dict)
        created_user_doc = self.users_collection.find_one({"_id": result.inserted_id})
        if not created_user_doc:
            logger.error(f"Failed to retrieve user after creation with ID: {result.inserted_id}")
            raise Exception("User creation failed unexpectedly.")
        return UserInDB(**created_user_doc)

    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID."""
        try:
            obj_id = ObjectId(user_id)
        except Exception:
            logger.warning(f"Invalid ObjectId format for user_id: {user_id}")
            return None
        user_doc = self.users_collection.find_one({"_id": obj_id})
        return UserInDB(**user_doc) if user_doc else None

    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email."""
        user_doc = self.users_collection.find_one({"email": email})
        return UserInDB(**user_doc) if user_doc else None

    def update_user(
        self, 
        user_id: str, 
        user_update: UserUpdate,
        current_user: UserInDB # User performing the update
    ) -> Optional[UserInDB]:
        """Update user information."""
        target_user = self.get_user_by_id(user_id)
        if not target_user:
            logger.warning(f"User not found for update with ID: {user_id}")
            return None 
            
        if current_user.role != UserRole.ADMIN and str(current_user.id) != user_id:
            logger.warning(f"User {current_user.email} (role: {current_user.role}) attempted to update user {user_id} without permission.")
            raise ValueError("Not enough permissions to update this user.")
            
        update_data = user_update.model_dump(exclude_unset=True)

        if 'role' in update_data and current_user.role != UserRole.ADMIN:
            logger.warning(f"User {current_user.email} attempted to change role of user {user_id} without ADMIN permission.")
            del update_data['role'] # Non-admins cannot change roles
        
        if 'role' in update_data and isinstance(update_data['role'], UserRole):
            update_data['role'] = update_data['role'].value

        if 'password' in update_data:
            if 'passwordConfirm' not in update_data or update_data['password'] != update_data['passwordConfirm']:
                raise ValueError("New passwords do not match for password update.")
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
            if 'passwordConfirm' in update_data: del update_data["passwordConfirm"]
        
        if not update_data: # No actual changes to make
            return target_user

        update_data["updated_at"] = datetime.utcnow()
        
        result = self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
             logger.error(f"Update failed: User {user_id} not found during update operation itself.")
             return None # Should have been caught by get_user_by_id, but as a safeguard

        updated_user_doc = self.get_user_by_id(user_id)
        return updated_user_doc

    def delete_user(self, user_id: str, current_user: UserInDB) -> bool:
        """Delete a user. Only ADMINs can delete users."""
        if current_user.role != UserRole.ADMIN:
            logger.warning(f"User {current_user.email} attempted to delete user {user_id} without ADMIN permission.")
            raise ValueError("Only administrators can delete users.")
        
        if str(current_user.id) == user_id:
            logger.warning(f"Admin user {current_user.email} attempted to delete themselves.")
            raise ValueError("Administrators cannot delete their own account.")

        try:
            obj_id = ObjectId(user_id)
        except Exception:
            logger.warning(f"Invalid ObjectId format for delete_user: {user_id}")
            return False
        
        target_user = self.get_user_by_id(user_id)
        if not target_user:
            logger.warning(f"User not found for deletion: {user_id}")
            return False
        
        # Prevent deletion of the last admin user if other users exist
        if target_user.role == UserRole.ADMIN:
            admin_count = self.users_collection.count_documents({'role': UserRole.ADMIN.value})
            if admin_count <= 1 and self.users_collection.count_documents({}) > 1:
                logger.warning(f"Attempt to delete the last admin user {user_id} while other users exist.")
                raise ValueError("Cannot delete the last administrator if other users exist.")

        result = self.users_collection.delete_one({"_id": obj_id})
        return result.deleted_count > 0

    def authenticate(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user with email and password."""
        user = self.get_user_by_email(email)
        if not user:
            return None
            
        if not verify_password(password, user.hashed_password):
            return None
            
        if not user.is_active:
            logger.warning(f"Authentication attempt for inactive user: {email}")
            raise ValueError("User account is disabled.")
        if not user.approved:
            logger.warning(f"Authentication attempt for unapproved user: {email}")
            raise ValueError("User account is not approved. Please contact administrator.")
            
        return user
        
    def generate_otp(self, user_id: str, expires_minutes: int = settings.OTP_EXPIRE_MINUTES) -> Tuple[str, datetime]:
        """Generate and store an OTP for password reset."""
        otp = str(random.randint(100000, 999999))
        otp_expires = datetime.utcnow() + timedelta(minutes=expires_minutes)
        
        self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"otp": otp, "otp_expires": otp_expires, "updated_at": datetime.utcnow()}}
        )
        return otp, otp_expires
        
    def verify_otp(self, user_id: str, otp: str) -> bool:
        """Verify if the provided OTP is valid for the user."""
        user_doc = self.users_collection.find_one({
            "_id": ObjectId(user_id),
            "otp": otp,
            "otp_expires": {"$gt": datetime.utcnow()}
        })
        return user_doc is not None
    
    def reset_password_with_otp(self, user_id: str, otp: str, new_password: str) -> bool:
        """Reset user's password using a valid OTP."""
        if not self.verify_otp(user_id, otp):
            logger.warning(f"Invalid or expired OTP provided for user_id: {user_id}")
            return False
            
        hashed_password = get_password_hash(new_password)
        result = self.users_collection.update_one(
            {"_id": ObjectId(user_id), "otp": otp}, # Ensure OTP is still the one verified
            {"$set": {"hashed_password": hashed_password, "updated_at": datetime.utcnow()},
             "$unset": {"otp": "", "otp_expires": ""}}
        )
        return result.modified_count > 0
        
    def update_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Update user's password by providing the current password."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
            
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
            
        hashed_password = get_password_hash(new_password)
        result = self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"hashed_password": hashed_password, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
        
    def initiate_password_reset(self, email: str) -> Optional[Tuple[str, str]]:
        """Initiate password reset by generating and returning an OTP."""
        user = self.get_user_by_email(email)
        if not user:
            return None
            
        otp, _ = self.generate_otp(str(user.id))
        return str(user.id), otp
        
    def deactivate_user(self, user_id: str, current_user: UserInDB) -> bool:
        """Deactivate a user account. Requires ADMIN or self."""
        if current_user.role != UserRole.ADMIN and str(current_user.id) != user_id:
            logger.warning(f"User {current_user.email} attempted to deactivate user {user_id} without permission.")
            raise ValueError("Not enough permissions to deactivate this user.")

        if str(current_user.id) == user_id and current_user.role == UserRole.ADMIN:
            admin_count = self.users_collection.count_documents({'role': UserRole.ADMIN.value, 'is_active': True})
            if admin_count <= 1:
                logger.warning(f"Admin user {current_user.email} attempted to deactivate themselves as the last active admin.")
                raise ValueError("Cannot deactivate the last active administrator.")

        result = self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
        
    def activate_user(self, user_id: str, current_user: UserInDB) -> bool:
        """Activate a user account. Requires ADMIN permission."""
        if current_user.role != UserRole.ADMIN:
            logger.warning(f"User {current_user.email} attempted to activate user {user_id} without ADMIN permission.")
            raise ValueError("Only administrators can activate users.")

        result = self.users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": True, "approved": True, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    def list_users(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UserInDB]:
        """Get list of users with optional filtering."""
        query: Dict[str, Any] = {}
        if filters:
            if "email" in filters and filters["email"]:
                query["email"] = {"$regex": filters['email'], "$options": "i"}
            if "full_name" in filters and filters["full_name"]:
                # Assuming full_name is a field or needs to be searched across first/last names
                # For simplicity, let's assume a 'full_name' field exists or adapt if necessary
                # If 'full_name' is not a direct field, this part might need adjustment based on User model
                query["$or"] = [
                    {"first_name": {"$regex": filters['full_name'], "$options": "i"}},
                    {"last_name": {"$regex": filters['full_name'], "$options": "i"}},
                    # If a combined 'full_name' field exists, add it here:
                    # {"full_name": {"$regex": filters['full_name'], "$options": "i"}}
                ]
            if "is_active" in filters and filters["is_active"] is not None:
                query["is_active"] = filters["is_active"]
            if "role" in filters and filters["role"]:
                try: query["role"] = UserRole(filters["role"]).value
                except ValueError: logger.warning(f"Invalid role filter: {filters['role']}")
            if "approved" in filters and filters["approved"] is not None:
                query["approved"] = filters["approved"]

        cursor = self.users_collection.find(query).skip(skip).limit(limit)
        return [UserInDB(**user_doc) for user_doc in cursor]

    def get_not_attended_users(self, event_id: str, organization_id: Optional[str] = None) -> List[UserInDB]:
        """Get users from an organization who did not attend a specific event."""
        try:
            parent_obj_id = ObjectId(event_id)
        except Exception:
            logger.warning(f"Invalid ObjectId for event_id in get_not_attended_users: {event_id}")
            return []

        # Get user_ids of those who attended the event and were marked present
        attended_user_id_docs = self.attendance_collection.find(
            {"parent_id": parent_obj_id, "parent_type": "event", "status": AttendanceStatus.PRESENT.value},
            {"user_id": 1} # Projection
        )
        attended_user_ids = [doc['user_id'] for doc in attended_user_id_docs]
        
        # Query for users in the specified organization (if provided) who are not in the attended list
        user_query: Dict[str, Any] = {"_id": {"$nin": attended_user_ids}}
        if organization_id:
            try: user_query["organization_id"] = ObjectId(organization_id)
            except Exception: 
                logger.warning(f"Invalid ObjectId for organization_id: {organization_id}")
                # Decide if to return [] or proceed without org filter. For now, proceed without.
                del user_query["organization_id"]
        
        users_cursor = self.users_collection.find(user_query)
        return [UserInDB(**user_doc) for user_doc in users_cursor]