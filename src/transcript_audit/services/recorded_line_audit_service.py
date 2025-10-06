import os
import logging
import json
import asyncio
from bson.objectid import ObjectId
from src.transcript_audit.schemas import TranscriptMessage, AuditStatus
from src.transcript_audit.util import convert_transcript_message_to_xml
from src.openai_client.client import OpenAIClient
from src.transcript_audit.prompts.recorded_line_phrase_audit import (
    get_human_transfer_detection_audit_prompt,
    get_recorded_line_phrase_audit_prompt,
)
from src.mongo_db import get_mongo_client
from src.transcript_audit.models import TranscriptAuditResult
from typing import Any

logger = logging.getLogger(__name__)


class RecordedLineAuditService:
    async def _get_human_agent_transfers(
        self, conversation: list[TranscriptMessage]
    ) -> list[int]:
        openai_client = OpenAIClient(model="chatgpt-4o-latest")

        xml_messages = []

        for index, message in enumerate(conversation):
            xml_messages.append(convert_transcript_message_to_xml(message, index))

        user_prompt = f"""
Here is the conversation history:
<messages>
{"\n".join(xml_messages)}
</messages>

Please return the indices of the messages where every time a new human agent comes on the line.
"""
        logger.info(
            "[RecordedLineAuditService._get_human_agent_transfers] Getting indices of human agent transfers"
        )

        response_format = {
            "type": "json_schema",
            "name": "human_transfer_indices",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "indices": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of message indices where a new human agent comes on the line",
                    }
                },
                "required": ["indices"],
                "additionalProperties": False,
            },
        }

        response = await openai_client.generate_response(
            system_prompt=get_human_transfer_detection_audit_prompt(),
            messages=[{"role": "user", "content": user_prompt}],
            response_format=response_format,
        )

        return json.loads(response)["indices"]

    async def _get_recorded_line_phrases(
        self,
        conversation: list[TranscriptMessage],
        human_transfer_indices: list[int],
        agent_name: str,
    ) -> dict[int, dict]:
        openai_client = OpenAIClient(model="chatgpt-4o-latest")
        start_offset = 3
        end_offset = 4

        logger.info(
            f"[RecordedLineAuditService._get_recorded_line_phrases] Getting recorded line phrases for {human_transfer_indices} transfers"
        )

        # Prepare all prompts and data first
        tasks = []
        transfer_indices_order = []

        for transfer_index in human_transfer_indices:
            conversation_chunk = conversation[
                transfer_index - start_offset : transfer_index + end_offset
            ]

            xml_messages = []

            for i, message in enumerate(conversation_chunk):
                xml_messages.append(
                    convert_transcript_message_to_xml(
                        message, transfer_index - start_offset + i
                    )
                )

            user_prompt = f"""
Here is the conversation chunk:
<messages>
{"\n".join(xml_messages)}
</messages>

Please return whether the voice agent explicitly stated that the call is on a recorded line when introducing itself to a human agent.
"""

            response_format = {
                "type": "json_schema",
                "name": "recorded_line_detection",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "has_recorded_line_phrase": {
                            "type": "boolean",
                            "description": "Whether the voice agent explicitly stated that the call is on a recorded line",
                        },
                        "index": {
                            "type": "integer",
                            "description": "The value of the <index> tag of the message where the voice agent introduced itself to the human staff and irrespective of whether it stated that the call is on a recorded line.",
                        },
                    },
                    "required": ["has_recorded_line_phrase", "index"],
                    "additionalProperties": False,
                },
            }

            task = openai_client.generate_response(
                system_prompt=get_recorded_line_phrase_audit_prompt(agent_name),
                messages=[{"role": "user", "content": user_prompt}],
                response_format=response_format,
            )
            tasks.append(task)
            transfer_indices_order.append(transfer_index)

        responses = await asyncio.gather(*tasks)

        audit_results: dict[int, dict] = {}

        for transfer_index, response in zip(transfer_indices_order, responses):
            result: dict = json.loads(response)

            audit_results[transfer_index] = {
                "has_recorded_line_phrase": result["has_recorded_line_phrase"],
                "recorded_line_phrase_index": result["index"],
            }

        return audit_results

    async def audit(self, transcript_audit_result_id: str, agent_name: str):
        try:
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

            logger.info("[RecordedLineAuditService.audit] Starting audit")
            human_transfer_indices: list[int] = await self._get_human_agent_transfers(
                conversation
            )
            logger.info(
                f"[RecordedLineAuditService.audit] Human transfer indices: {human_transfer_indices}"
            )

            recorded_line_phrases = await self._get_recorded_line_phrases(
                conversation, human_transfer_indices, agent_name
            )

            recorded_lines_audit: dict[str, Any] = {
                "total_human_transfers": len(human_transfer_indices),
                "total_recorded_line_phrases": 0,
                "auditted_chunks": [],
            }

            for index, phrase_result in recorded_line_phrases.items():
                recorded_line_phrase_index: int = phrase_result[
                    "recorded_line_phrase_index"
                ]

                human_transfer_message: TranscriptMessage = conversation[index]
                recorded_line_phrase_message: TranscriptMessage = conversation[
                    recorded_line_phrase_index
                ]

                if phrase_result["has_recorded_line_phrase"]:
                    recorded_lines_audit["total_recorded_line_phrases"] += 1

                recorded_lines_audit["auditted_chunks"].append(
                    {
                        "has_recorded_line_phrase": phrase_result[
                            "has_recorded_line_phrase"
                        ],
                        "human_transfer_message_id": human_transfer_message.id,
                        "human_transfer_message_content": human_transfer_message.content,
                        "recorded_line_phrase_message_id": recorded_line_phrase_message.id,
                        "recorded_line_phrase_message_content": recorded_line_phrase_message.content,
                    }
                )

            logger.info(
                f"Saving audit results to database for transcript audit result id: {transcript_audit_result_id}"
            )

            await mongo_client.update_one(
                TranscriptAuditResult.collection_name(),
                {"_id": ObjectId(transcript_audit_result_id)},
                {"$set": {"audit_results.recorded_line_phrases": recorded_lines_audit, "status.recorded_line_phrases": AuditStatus.COMPLETED}},
            )
            logger.info(f"Audit results saved to database for transcript audit result id: {transcript_audit_result_id}")

            return recorded_lines_audit
        except Exception as e:
            await mongo_client.update_one(
                TranscriptAuditResult.collection_name(),
                {"_id": ObjectId(transcript_audit_result_id)},
                {"$set": {"status.recorded_line_phrases": AuditStatus.FAILED}},
            )
            logger.error(f"[RecordedLineAuditService.audit] Error: {e}")
            raise e
