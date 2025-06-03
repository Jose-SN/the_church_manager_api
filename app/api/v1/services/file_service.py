import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple

import aiofiles
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.file import File as FileModel
from app.schemas.file import FileInDB

class FileService:
    """Service for handling file operations"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.allowed_extensions = {
            'image': {'jpg', 'jpeg', 'png', 'gif', 'webp'},
            'document': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'},
            'video': {'mp4', 'webm', 'mov'},
            'audio': {'mp3', 'wav', 'ogg'},
        }
        self.max_file_size = settings.MAX_FILE_SIZE  # in bytes
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension in lowercase"""
        return Path(filename).suffix.lower().lstrip('.')
    
    def _get_file_type(self, extension: str) -> str:
        """Determine file type based on extension"""
        for file_type, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return file_type
        return 'other'
    
    def _is_extension_allowed(self, extension: str) -> bool:
        """Check if file extension is allowed"""
        return any(extension in extensions for extensions in self.allowed_extensions.values())
    
    async def upload_file(
        self,
        file: UploadFile,
        uploaded_by: str,
        organization_id: str,
        db: AsyncSession
    ) -> FileInDB:
        """
        Upload a file to the server and save its metadata to the database
        """
        # Validate file size
        file.file.seek(0, 2)  # Go to end of file
        file_size = file.file.tell()
        file.file.seek(0)  # Go back to start
        
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size: {self.max_file_size / (1024 * 1024)}MB"
            )
        
        # Validate file extension
        file_extension = self._get_file_extension(file.filename)
        if not self._is_extension_allowed(file_extension):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed: {file_extension}"
            )
        
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_type = self._get_file_type(file_extension)
        file_path = self.upload_dir / f"{file_id}.{file_extension}"
        
        # Save file
        try:
            async with aiofiles.open(file_path, 'wb') as out_file:
                while content := await file.read(1024 * 1024):  # 1MB chunks
                    await out_file.write(content)
        except Exception as e:
            # Clean up if something goes wrong
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving file: {str(e)}"
            )
        
        # Save file metadata to database
        db_file = FileModel(
            id=file_id,
            original_filename=file.filename,
            file_extension=file_extension,
            file_type=file_type,
            file_size=file_size,
            mime_type=file.content_type,
            file_path=str(file_path),
            uploaded_by=uploaded_by,
            organization_id=organization_id,
        )
        
        db.add(db_file)
        await db.commit()
        await db.refresh(db_file)
        
        return db_file
    
    async def get_file_info(self, file_id: str, db: AsyncSession) -> Optional[FileInDB]:
        """Get file metadata by ID"""
        result = await db.execute(
            select(FileModel).where(FileModel.id == file_id)
        )
        return result.scalars().first()
    
    async def download_file(self, file_id: str, db: AsyncSession) -> Tuple[Path, str]:
        """Get file path and filename for downloading"""
        file_info = await self.get_file_info(file_id, db)
        
        if not file_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        file_path = Path(file_info.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        
        return file_path, file_info.original_filename
    
    async def list_files(
        self,
        organization_id: str,
        skip: int = 0,
        limit: int = 100,
        file_type: Optional[str] = None,
        db: AsyncSession = None
    ) -> List[FileInDB]:
        """List all files with optional filtering"""
        query = select(FileModel).where(FileModel.organization_id == organization_id)
        
        if file_type:
            query = query.where(FileModel.file_type == file_type.lower())
        
        result = await db.execute(
            query.order_by(FileModel.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def delete_file(self, file_id: str, db: AsyncSession) -> bool:
        """Delete a file and its metadata"""
        file_info = await self.get_file_info(file_id, db)
        
        if not file_info:
            return False
        
        # Delete file from disk
        file_path = Path(file_info.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error deleting file: {str(e)}"
                )
        
        # Delete from database
        await db.delete(file_info)
        await db.commit()
        
        return True

# Singleton instance
file_service = FileService()

def get_file_service() -> FileService:
    return file_service
