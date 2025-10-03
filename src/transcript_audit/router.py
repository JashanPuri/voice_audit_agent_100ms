from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from typing import Optional
import json
import logging
from bson.objectid import ObjectId
from src.transcript_audit.models import TranscriptAuditResult
from src.transcript_audit.services.recorded_line_audit_service import (
    RecordedLineAuditService,
)
from src.transcript_audit.schemas import AuditStatus, TranscriptMessage, AuditType
from src.mongo_db import get_mongo_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/transcript/audits")
async def audit_transcript(
    transcript_file: UploadFile = File(
        ..., description="JSON file containing transcript data"
    ),
    audit_types: list[AuditType] = Form(
        ..., description="List of audit types to perform"
    ),
    recorded_line_audit_service: RecordedLineAuditService = Depends(
        RecordedLineAuditService
    ),
):
    try:
        mongo_client = get_mongo_client()

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

        # Note: Storing it initially to make it avaialble for workflows running as workers via the task queues
        transcript_audit_result = TranscriptAuditResult(
            transcript_file_name=transcript_file.filename,
            audit_types=audit_types,
            conversation_history=conversation,
            status={audit_type: AuditStatus.PENDING for audit_type in audit_types},
        )

        transcript_audit_result_id = await mongo_client.insert_one(
            TranscriptAuditResult.collection_name(),
            document=transcript_audit_result.to_mongo(),
        )

        transcript_audit_result.id = transcript_audit_result_id

        logger.info(f"[audit_transcript] Transcript audit result id: {transcript_audit_result_id}")

        # TODO: Make the audit workflows async by using task queues
        if AuditType.RECORDED_LINE_PHRASES in audit_types:
            await recorded_line_audit_service.audit(
                transcript_audit_result_id, f"{agent_first_name} {agent_last_name}"
            )

    except json.JSONDecodeError as e:
        return {"error": "Invalid JSON file", "message": str(e)}

    return transcript_audit_result


# TODO: Add pagination
@router.get("/transcript/audits")
async def get_transcript_audits():
    mongo_client = get_mongo_client()
    transcript_audits = await mongo_client.find_many(TranscriptAuditResult.collection_name(), {})
    return [
        TranscriptAuditResult(**transcript_audit) for transcript_audit in transcript_audits
    ]

@router.get("/transcript/audits/{transcript_audit_id}")
async def get_transcript_audit(transcript_audit_id: str):
    if not ObjectId.is_valid(transcript_audit_id):
        raise HTTPException(status_code=400, detail="Invalid transcript audit id")
    
    mongo_client = get_mongo_client()
    transcript_audit = await mongo_client.find_one(TranscriptAuditResult.collection_name(), {"_id": transcript_audit_id})
    return TranscriptAuditResult(**transcript_audit)
