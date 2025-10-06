from pydantic import BaseModel
from enum import Enum

class AuditType(str, Enum):
    RECORDED_LINE_PHRASES = "recorded_line_phrases"
    SECTION_BREAKDOWN = "section_breakdown"

class AuditStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptMessage(BaseModel):
    id: str
    role: str
    content: str

