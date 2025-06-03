from typing import List, Optional
from pymongo.database import Database
from bson import ObjectId
from datetime import datetime

from app.models.organization import OrganizationInDB # TODO: Update this import path
from app.schemas.organization import Organization, OrganizationCreate, OrganizationUpdate # TODO: Update this import path if necessary
# from app.models.user import User # For future use with current_user for permissions

class OrganizationService:
    def __init__(self, db: Database):
        self.db = db
        self.collection = self.db['organizations']

    def _db_to_schema(self, db_org: OrganizationInDB) -> Organization:
        """Converts a DB model instance to a schema model instance."""
        org_dict = db_org.dict(by_alias=True)
        org_dict['id'] = str(org_dict.pop('_id'))
        return Organization(**org_dict)

    def create_organization(self, org_create: OrganizationCreate) -> Organization:
        now = datetime.utcnow()
        org_data = org_create.dict()
        org_data['created_at'] = now
        org_data['updated_at'] = now
        
        # Convert to OrganizationInDB for validation before insertion (optional, but good practice)
        # org_in_db_data = OrganizationInDB(**org_data).dict(by_alias=True)
        # For now, directly insert if schemas are aligned or handle specific fields like _id manually

        result = self.collection.insert_one(org_data)
        created_org_doc = self.collection.find_one({'_id': result.inserted_id})
        if created_org_doc:
            return self._db_to_schema(OrganizationInDB(**created_org_doc))
        # This part should ideally not be reached if insert was successful
        raise Exception("Failed to create organization or retrieve after creation") 

    def get_organization_by_id(self, org_id: str) -> Optional[Organization]:
        try:
            obj_id = ObjectId(org_id)
        except Exception:
            return None # Invalid ObjectId format
        db_org = self.collection.find_one({'_id': obj_id})
        if db_org:
            return self._db_to_schema(OrganizationInDB(**db_org))
        return None

    def list_organizations(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        organizations_cursor = self.collection.find().skip(skip).limit(limit)
        return [self._db_to_schema(OrganizationInDB(**org_doc)) for org_doc in organizations_cursor]

    def update_organization(self, org_id: str, org_update: OrganizationUpdate) -> Optional[Organization]:
        try:
            obj_id = ObjectId(org_id)
        except Exception:
            return None # Invalid ObjectId format

        update_data = org_update.dict(exclude_unset=True)
        if not update_data:
            # If there's nothing to update, maybe return the existing org or an error/specific response
            return self.get_organization_by_id(org_id) 

        update_data['updated_at'] = datetime.utcnow()

        result = self.collection.update_one(
            {'_id': obj_id},
            {'$set': update_data}
        )
        if result.matched_count:
            updated_org_doc = self.collection.find_one({'_id': obj_id})
            if updated_org_doc:
                return self._db_to_schema(OrganizationInDB(**updated_org_doc))
        return None

    def delete_organization(self, org_id: str) -> bool:
        try:
            obj_id = ObjectId(org_id)
        except Exception:
            return False # Invalid ObjectId format
        result = self.collection.delete_one({'_id': obj_id})
        return result.deleted_count > 0
