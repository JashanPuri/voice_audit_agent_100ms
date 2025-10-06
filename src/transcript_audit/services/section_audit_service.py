import logging
import json
import asyncio
from src.mongo_db import get_mongo_client
from bson.objectid import ObjectId
from src.transcript_audit.schemas import TranscriptMessage, AuditStatus
from src.transcript_audit.models import TranscriptAuditResult
from src.openai_client.client import OpenAIClient
from src.transcript_audit.prompts.section_breakdown_audit import (
    get_section_breakdown_audit_prompt,
)
from src.transcript_audit.util import convert_transcript_message_to_xml

logger = logging.getLogger(__name__)


class SectionAuditService:

    async def _get_section_breakdown(
        self, conversation: list[TranscriptMessage], agent_name: str
    ) -> list[dict]:
        openai_client = OpenAIClient(model="chatgpt-4o-latest")

        xml_messages = []

        for index, message in enumerate(conversation):
            xml_messages.append(convert_transcript_message_to_xml(message, index))
        user_prompt = f"""
Here is the conversation history:
<messages>
{"\n".join(xml_messages)}
</messages>

Please return the section breakdown of the conversation in the specified JSON format.
"""

        response_format = {
            "type": "json_schema",
            "name": "conversation_section_breakdown",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "sections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "section_type": {
                                    "type": "string",
                                    "enum": [
                                        "IVR",
                                        "INTRODUCTION",
                                        "TRANSFER",
                                        "BENEFITS_COLLECTION",
                                    ],
                                },
                                "start_index": {"type": "integer"},
                                "end_index": {"type": "integer"},
                            },
                            "required": ["section_type", "start_index", "end_index"],
                            "additionalProperties": False,
                        },
                        "description": "List of sections in the conversation",
                    }
                },
                "required": ["sections"],
                "additionalProperties": False,
            },
        }

        response = await openai_client.generate_response(
            system_prompt=get_section_breakdown_audit_prompt(agent_name),
            messages=[{"role": "user", "content": user_prompt}],
            response_format=response_format,
        )

        return json.loads(response)["sections"]

    async def audit(self, transcript_audit_result_id: str, agent_name: str):
        mongo_client = get_mongo_client()
        transcript_audit_result_document = await mongo_client.find_one(
            TranscriptAuditResult.collection_name(),
            {"_id": ObjectId(transcript_audit_result_id)},
        )

        if not transcript_audit_result_document:
            raise ValueError(
                f"Transcript audit result with id {transcript_audit_result_id} not found"
            )

        transcript_audit_result = TranscriptAuditResult(
            **transcript_audit_result_document
        )

        conversation = transcript_audit_result.conversation_history

        sections: list[dict] = await self._get_section_breakdown(conversation, agent_name)

        section_breakdown: list[dict] = []

        for section in sections:
            section_breakdown.append({
                "section_type": section["section_type"],
                "start_index": section["start_index"],
                "end_index": section["end_index"],
                "start_message_id": conversation[section["start_index"]].id,
                "end_message_id": conversation[section["end_index"]].id,
            })

        section_audit = {
            "section_breakdown": section_breakdown,
            "total_sections": len(section_breakdown),
        }

        await mongo_client.update_one(
            TranscriptAuditResult.collection_name(),
            {"_id": ObjectId(transcript_audit_result_id)},
            {"$set": {"audit_results.section_breakdown": section_audit, "status.section_breakdown": AuditStatus.COMPLETED}},
        )

        return section_audit

