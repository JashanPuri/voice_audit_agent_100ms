from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from src.transcript_audit.schemas import AuditType, AuditStatus
from src.transcript_audit.schemas import TranscriptMessage

class TranscriptAuditResult(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    transcript_file_name: str
    audit_types: List[AuditType] = Field(default_factory=list)
    conversation_history: List[TranscriptMessage] = Field(default_factory=list)
    status: AuditStatus = Field(default=AuditStatus.PENDING)
    audit_results: Optional[Dict[AuditType, Any]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @staticmethod
    def collection_name() -> str:
        return "TranscriptAuditResults"
    
    def to_mongo(self) -> dict:
        data = self.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        return data

