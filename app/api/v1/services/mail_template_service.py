from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mail_template import MailTemplate as MailTemplateModel
from app.schemas.mail_template import MailTemplateCreate, MailTemplateInDB, MailTemplateUpdate

class MailTemplateService:
    """Service for handling email template operations"""
    
    async def create_template(
        self,
        template_in: MailTemplateCreate,
        created_by: str,
        organization_id: str,
        db: AsyncSession
    ) -> MailTemplateInDB:
        """
        Create a new mail template
        """
        # Check if template with same name and type exists in organization
        existing_template = await self._get_template_by_name_and_type(
            name=template_in.name,
            template_type=template_in.template_type,
            organization_id=organization_id,
            db=db
        )
        
        if existing_template:
            # Update existing template if found
            return await self.update_template(
                template_id=str(existing_template.id),
                template_in=MailTemplateUpdate(**template_in.dict()),
                db=db
            )
        
        # Create new template
        template_data = template_in.dict()
        template_data['created_by'] = created_by
        template_data['organization_id'] = organization_id
        
        db_template = MailTemplateModel(**template_data)
        db.add(db_template)
        await db.commit()
        await db.refresh(db_template)
        
        return db_template
    
    async def get_template(
        self,
        template_id: str,
        db: AsyncSession
    ) -> Optional[MailTemplateInDB]:
        """
        Get a template by ID
        """
        result = await db.execute(
            select(MailTemplateModel).where(MailTemplateModel.id == template_id)
        )
        return result.scalars().first()
    
    async def _get_template_by_name_and_type(
        self,
        name: str,
        template_type: str,
        organization_id: str,
        db: AsyncSession
    ) -> Optional[MailTemplateInDB]:
        """
        Get a template by name and type within an organization
        """
        result = await db.execute(
            select(MailTemplateModel)
            .where(
                and_(
                    MailTemplateModel.name == name,
                    MailTemplateModel.template_type == template_type,
                    MailTemplateModel.organization_id == organization_id,
                    MailTemplateModel.deleted_at.is_(None)
                )
            )
        )
        return result.scalars().first()
    
    async def get_template_by_name(
        self,
        name: str,
        organization_id: str,
        db: AsyncSession
    ) -> Optional[MailTemplateInDB]:
        """
        Get the latest version of a template by name
        """
        result = await db.execute(
            select(MailTemplateModel)
            .where(
                and_(
                    MailTemplateModel.name == name,
                    MailTemplateModel.organization_id == organization_id,
                    MailTemplateModel.is_active == True,
                    MailTemplateModel.deleted_at.is_(None)
                )
            )
            .order_by(MailTemplateModel.version.desc())
        )
        return result.scalars().first()
    
    async def list_templates(
        self,
        organization_id: str,
        template_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = None
    ) -> List[MailTemplateInDB]:
        """
        List templates with optional filtering
        """
        query = select(MailTemplateModel).where(
            and_(
                MailTemplateModel.organization_id == organization_id,
                MailTemplateModel.deleted_at.is_(None)
            )
        )
        
        if template_type:
            query = query.where(MailTemplateModel.template_type == template_type)
        
        # Get only the latest version of each template
        subquery = (
            select(
                MailTemplateModel.name,
                MailTemplateModel.template_type,
                db.func.max(MailTemplateModel.version).label('max_version')
            )
            .where(
                and_(
                    MailTemplateModel.organization_id == organization_id,
                    MailTemplateModel.deleted_at.is_(None)
                )
            )
            .group_by(
                MailTemplateModel.name,
                MailTemplateModel.template_type
            )
            .subquery()
        )
        
        query = (
            select(MailTemplateModel)
            .join(
                subquery,
                and_(
                    MailTemplateModel.name == subquery.c.name,
                    MailTemplateModel.template_type == subquery.c.template_type,
                    MailTemplateModel.version == subquery.c.max_version
                )
            )
            .where(
                and_(
                    MailTemplateModel.organization_id == organization_id,
                    MailTemplateModel.deleted_at.is_(None)
                )
            )
            .order_by(MailTemplateModel.name)
        )
        
        result = await db.execute(
            query.offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def update_template(
        self,
        template_id: str,
        template_in: MailTemplateUpdate,
        db: AsyncSession
    ) -> MailTemplateInDB:
        """
        Update a template by creating a new version
        """
        existing_template = await self.get_template(template_id, db)
        if not existing_template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Create a new version of the template
        template_data = template_in.dict(exclude_unset=True)
        template_data['version'] = existing_template.version + 1
        template_data['created_by'] = existing_template.created_by
        template_data['organization_id'] = existing_template.organization_id
        
        # Deactivate old version
        existing_template.is_active = False
        db.add(existing_template)
        
        # Create new version
        new_template = MailTemplateModel(**template_data)
        db.add(new_template)
        
        await db.commit()
        await db.refresh(new_template)
        
        return new_template
    
    async def delete_template(
        self,
        template_id: str,
        db: AsyncSession
    ) -> bool:
        """
        Soft delete a template
        """
        template = await self.get_template(template_id, db)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        # Soft delete by setting deleted_at
        template.deleted_at = datetime.utcnow()
        
        db.add(template)
        await db.commit()
        
        return True

# Singleton instance
mail_template_service = MailTemplateService()

def get_mail_template_service() -> MailTemplateService:
    return mail_template_service
