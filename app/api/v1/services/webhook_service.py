from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from app.database.connection import get_database
from app.models.webhook import WebhookConfig, WebhookLog, WebhookEvent

class WebhookService:
    """Service class for webhook operations."""
    
    def __init__(self):
        self.db = get_database()
        self.configs_collection = self.db.webhook_configs
        self.logs_collection = self.db.webhook_logs

    async def create_webhook_config(self, config: WebhookConfig) -> WebhookConfig:
        """
        Create a new webhook configuration.
        """
        config_dict = config.model_dump()
        config_dict["created_at"] = datetime.utcnow()
        config_dict["updated_at"] = datetime.utcnow()
        
        result = await self.configs_collection.insert_one(config_dict)
        webhook = await self.configs_collection.find_one({"_id": result.inserted_id})
        return WebhookConfig(**webhook)

    async def get_webhook_config(self, webhook_id: str) -> Optional[WebhookConfig]:
        """
        Get webhook configuration by ID.
        """
        webhook = await self.configs_collection.find_one({"_id": ObjectId(webhook_id)})
        return WebhookConfig(**webhook) if webhook else None

    async def get_webhook_configs(self, skip: int = 0, limit: int = 100) -> List[WebhookConfig]:
        """
        Get list of webhook configurations.
        """
        webhooks = await self.configs_collection.find().skip(skip).limit(limit).to_list(100)
        return [WebhookConfig(**webhook) for webhook in webhooks]

    async def update_webhook_config(
        self, 
        webhook_id: str, 
        config: WebhookConfig
    ) -> WebhookConfig:
        """
        Update webhook configuration.
        """
        # Check if webhook exists
        webhook = await self.get_webhook_config(webhook_id)
        if not webhook:
            raise ValueError("Webhook configuration not found")
            
        # Update webhook
        update_data = config.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        await self.configs_collection.update_one(
            {"_id": ObjectId(webhook_id)},
            {"$set": update_data}
        )
        
        # Get updated webhook
        updated_webhook = await self.get_webhook_config(webhook_id)
        if not updated_webhook:
            raise ValueError("Webhook configuration not found after update")
        return updated_webhook

    async def delete_webhook_config(self, webhook_id: str) -> None:
        """
        Delete webhook configuration.
        """
        await self.configs_collection.delete_one({"_id": ObjectId(webhook_id)})

    async def process_webhook_event(self, event: WebhookEvent) -> WebhookLog:
        """
        Process incoming webhook event.
        """
        # Find matching webhook configurations
        configs = await self.configs_collection.find({
            "events": {"$in": [event.event]},
            "active": True
        }).to_list(100)
        
        # Process each matching webhook
        logs = []
        for config in configs:
            # TODO: Implement actual webhook processing logic
            # This would typically involve making HTTP requests to the webhook URL
            # with the event payload and handling the response
            
            log = WebhookLog(
                webhook_id=str(config["_id"]),
                event=event.event,
                payload=event.payload,
                response_status=200,  # This would be the actual response status
                response_body="{}",  # This would be the actual response body
                timestamp=datetime.utcnow()
            )
            
            log_dict = log.model_dump()
            result = await self.logs_collection.insert_one(log_dict)
            log = await self.logs_collection.find_one({"_id": result.inserted_id})
            logs.append(WebhookLog(**log))
        
        return logs[0] if logs else None

    async def get_webhook_logs(
        self, 
        webhook_id: Optional[str] = None,
        event: Optional[str] = None,
        limit: int = 100
    ) -> List[WebhookLog]:
        """
        Get webhook logs.
        """
        query = {}
        if webhook_id:
            query["webhook_id"] = webhook_id
        if event:
            query["event"] = event
        
        logs = await self.logs_collection.find(query).sort("timestamp", -1).limit(limit).to_list(100)
        return [WebhookLog(**log) for log in logs]
