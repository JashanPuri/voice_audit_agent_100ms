from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from typing import Optional
import json
import logging
import asyncio
from bson.objectid import ObjectId
from src.transcript_audit.models import TranscriptAuditResult
from src.transcript_audit.services.recorded_line_audit_service import (
    RecordedLineAuditService,
)
from src.transcript_audit.schemas import AuditStatus, TranscriptMessage, AuditType
from src.mongo_db import get_mongo_client
from src.transcript_audit.services.section_audit_service import SectionAuditService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/transcript/audits")
async def audit_transcript(
    transcript_file: UploadFile = File(
        ..., description="JSON or NDJSON file containing transcript data"
    ),
    audit_types: list[AuditType] = Form(
        ..., description="List of audit types to perform"
    ),
    recorded_line_audit_service: RecordedLineAuditService = Depends(
        RecordedLineAuditService
    ),
    section_audit_service: SectionAuditService = Depends(SectionAuditService),
):
    try:
        mongo_client = get_mongo_client()

        content = await transcript_file.read()

        try:
            json_content: dict = json.loads(content)
        except json.JSONDecodeError:
            text_content = content.decode('utf-8')
            lines = text_content.strip().split('\n')

            last_json_object = None
            for line in reversed(lines):
                line = line.strip()
                if line:
                    try:
                        last_json_object = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue
            
            if last_json_object is None:
                raise ValueError("No valid JSON object found in NDJSON file")
            
            json_content = last_json_object

        context = json_content.get("data", {}).get("context", {})
        variables = context.get("variables", {})
        user_data = context.get("user_data", {})

        conversation_history = variables.get("review_conversation_history", [])
        agent_first_name = variables.get("agent_first_name", "")
        agent_last_name = variables.get("agent_last_name", "")

        org_id = user_data.get("org_id", "")
        session_id = user_data.get("session_id", "")

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
            org_id=org_id,
            session_id=session_id,
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

        logger.info(
            f"[audit_transcript] Transcript audit result id: {transcript_audit_result_id}"
        )

        # Run audit workflows concurrently
        audit_tasks = []
        
        if AuditType.RECORDED_LINE_PHRASES in audit_types:
            audit_tasks.append(
                recorded_line_audit_service.audit(
                    transcript_audit_result_id, f"{agent_first_name} {agent_last_name}"
                )
            )

        if AuditType.SECTION_BREAKDOWN in audit_types:
            audit_tasks.append(
                section_audit_service.audit(
                    transcript_audit_result_id, f"{agent_first_name} {agent_last_name}"
                )
            )
        
        if audit_tasks:
            await asyncio.gather(*audit_tasks)

    except json.JSONDecodeError as e:
        return {"error": "Invalid JSON file", "message": str(e)}
    except ValueError as e:
        return {"error": "Invalid file format", "message": str(e)}

    return transcript_audit_result


# TODO: Add pagination
@router.get("/transcript/audits")
async def get_transcript_audits():
    mongo_client = get_mongo_client()
    transcript_audits = await mongo_client.find_many(
        TranscriptAuditResult.collection_name(), {}
    )
    return [
        TranscriptAuditResult(**transcript_audit)
        for transcript_audit in transcript_audits
    ]


@router.get("/transcript/audits/{transcript_audit_id}")
async def get_transcript_audit(transcript_audit_id: str):
    if not ObjectId.is_valid(transcript_audit_id):
        raise HTTPException(status_code=400, detail="Invalid transcript audit id")

    mongo_client = get_mongo_client()
    transcript_audit = await mongo_client.find_one(
        TranscriptAuditResult.collection_name(), {"_id": transcript_audit_id}
    )
    return TranscriptAuditResult(**transcript_audit)
