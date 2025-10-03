import os
import logging
import json
import asyncio
from src.transcript_audit.schemas import TranscriptMessage
from src.transcript_audit.util import convert_transcript_message_to_xml
from src.openai_client.client import OpenAIClient
from src.transcript_audit.prompts.recorded_line_phrase_audit import (
    get_human_transfer_detection_audit_prompt,
    get_recorded_line_phrase_audit_prompt,
)

logger = logging.getLogger(__name__)


class RecordedLineAuditService:
    def __init__(self):
        pass

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
        self, conversation: list[TranscriptMessage], human_transfer_indices: list[int], agent_name: str
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

            logger.info(
                f"[RecordedLineAuditService._get_recorded_line_phrases] User prompt for transfer {transfer_index}: {conversation[transfer_index].content}"
            )

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
                            "description": "The value of the <index> tag of the message where the voice agent explicitly stated that the call is on a recorded line. Do not include if the voice agent did not state that the call is on a recorded line.",
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

        logger.info(
            f"[RecordedLineAuditService._get_recorded_line_phrases] Executing {len(tasks)} API calls concurrently"
        )
        responses = await asyncio.gather(*tasks)

        audit_results: dict[int, dict] = {}
        
        for transfer_index, response in zip(transfer_indices_order, responses):
            logger.info(
                f"[RecordedLineAuditService._get_recorded_line_phrases] Result for transfer {transfer_index}: {response}"
            )

            result: dict = json.loads(response)

            audit_results[transfer_index] = {
                "has_recorded_line_phrase": result["has_recorded_line_phrase"],
            }

            if result["has_recorded_line_phrase"] is True:
                audit_results[transfer_index]["recorded_line_phrase_index"] = result[
                    "index"
                ]

        return audit_results

    async def audit(self, conversation: list[TranscriptMessage], agent_name: str):
        logger.info("[RecordedLineAuditService.audit] Starting audit")
        human_transfer_indices: list[int] = await self._get_human_agent_transfers(
            conversation
        )
        logger.info(
            f"[RecordedLineAuditService.audit] Human transfer indices: {human_transfer_indices}"
        )

        for index in human_transfer_indices:
            logger.info(
                f"[RecordedLineAuditService.audit] Message at index {index} => {conversation[index].role}: {conversation[index].content}"
            )

        recorded_line_phrases = await self._get_recorded_line_phrases(
            conversation, human_transfer_indices, agent_name
        )

        audit_results: dict[int, dict] = {}

        for index, result in recorded_line_phrases.items():
            human_transfer_message = conversation[index]
            recorded_line_phrase_message = None

            if result["has_recorded_line_phrase"] is True:
                recorded_line_phrase_message = conversation[
                    result["recorded_line_phrase_index"]
                ]

            audit_results[human_transfer_message.id] = {
                "human_transfer_message_id": human_transfer_message.id,
                "has_recorded_line_phrase": result["has_recorded_line_phrase"],
                "recorded_line_phrase_message_id": (
                    recorded_line_phrase_message.id
                    if recorded_line_phrase_message is not None
                    else None
                ),
            }

        return audit_results
