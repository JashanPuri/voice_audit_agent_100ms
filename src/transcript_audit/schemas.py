from pydantic import BaseModel
from enum import Enum


class AuditType(str, Enum):
    RECORDED_LINE_PHRASES = "recorded_line_phrases"


class TranscriptMessage(BaseModel):
    id: str
    role: str
    content: str

