from fastapi import APIRouter, File, UploadFile, Form, Depends
from typing import Optional
import json
import logging
from src.transcript_audit.services.recorded_line_audit_service import (
    RecordedLineAuditService,
)
from src.transcript_audit.schemas import TranscriptMessage, AuditType

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/transcript/audit")
async def audit_transcript(
    transcript_file: UploadFile = File(
        ..., description="JSON file containing transcript data"
    ),
    audit_types: list[AuditType] = Form(..., description="List of audit types to perform"),
    recorded_line_audit_service: RecordedLineAuditService = Depends(
        RecordedLineAuditService
    ),
):
    try:
        content = await transcript_file.read()

        json_content: dict = json.loads(content)

        conversation_history = (
            json_content.get("data", {})
            .get("context", {})
            .get("variables", {})
            .get("review_conversation_history", [])
        )
        agent_first_name = (
            json_content.get("data", {})
            .get("context", {})
            .get("variables", {})
            .get("agent_first_name", "")
        )
        agent_last_name = (
            json_content.get("data", {})
            .get("context", {})
            .get("variables", {})
            .get("agent_last_name", "")
        )

        logger.info(
            f"[audit_transcript] Conversation history: {len(conversation_history)}"
        )

        conversation: list[TranscriptMessage] = []

        for message in conversation_history:
            conversation.append(
                TranscriptMessage(
                    id=message["_id"], role=message["role"], content=message["content"]
                )
            )

        response = {}

        if AuditType.RECORDED_LINE_PHRASES in audit_types:
            response["recorded_line_phrases"] = await recorded_line_audit_service.audit(
                conversation, f"{agent_first_name} {agent_last_name}"
            )

    except json.JSONDecodeError as e:
        return {"error": "Invalid JSON file", "message": str(e)}

    return {
        "message": "Transcript audited successfully",
        "file_name": transcript_file.filename,
        "audit_types": audit_types,
        "audit_results": response,
    }
