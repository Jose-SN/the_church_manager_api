from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

# Association table for many-to-many relationship between users and roles
user_role = Table(
    'user_role',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('role_id', Integer, ForeignKey('role.id'))
)

class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    
    # Relationships
    roles = relationship("Role", secondary=user_role, back_populates="users")
    events_created = relationship("Event", back_populates="creator")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.email}>"


class Role(Base):
    __tablename__ = "role"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    
    # Relationships
    users = relationship("User", secondary=user_role, back_populates="roles")
    permissions = relationship("Permission", secondary="role_permission", back_populates="roles")
    
    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(Base):
    __tablename__ = "permission"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    
    # Relationships
    roles = relationship("Role", secondary="role_permission", back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission {self.name}>"


# Association table for many-to-many relationship between roles and permissions
role_permission = Table(
    'role_permission',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('role.id')),
    Column('permission_id', Integer, ForeignKey('permission.id'))
)
