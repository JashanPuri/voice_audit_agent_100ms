import pytest
import json
import asyncio
from src.openai_client.client import OpenAIClient
from src.transcript_audit.prompts.recorded_line_phrase_audit import (
    get_human_transfer_detection_audit_prompt,
)
from dotenv import load_dotenv

load_dotenv()


async def call_and_verify(
    openai_client: OpenAIClient,
    system_prompt: str,
    user_prompt: str,
    response_format: dict,
    iteration: int,
    total: int,
) -> dict:
    response = await openai_client.generate_response(
        system_prompt=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        response_format=response_format,
    )
    
    parsed = json.loads(response)
    assert "indices" in parsed, f"Iteration {iteration}: Response must contain 'indices' key"
    assert isinstance(parsed["indices"], list), f"Iteration {iteration}: indices must be a list"
    assert all(isinstance(x, int) for x in parsed["indices"]), f"Iteration {iteration}: All indices must be integers"
    
    print(f"Iteration {iteration}/{total}: Valid - indices: {parsed['indices']}")
    return parsed


@pytest.mark.asyncio
async def test_human_transfer_indices_prompt_format():
    """
    Test that the human transfer detection prompt returns the correct JSON format.
    Runs 50 times concurrently in batches of 10 to ensure consistency.
    """
    # Setup
    openai_client = OpenAIClient(model="chatgpt-4o-latest")
    
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
    
    conversation = """<messages>
<message>
<index>0</index>
<role>user</role>
<content>Thank you for calling ABC Insurance. Press 1 for claims, press 2 for benefits.</content>
</message>
<message>
<index>1</index>
<role>assistant</role>
<content>Representative</content>
</message>
<message>
<index>2</index>
<role>user</role>
<content>Please hold while I connect you to a representative.</content>
</message>
<message>
<index>3</index>
<role>user</role>
<content>Hi, this is Sarah with Member Services. How can I help you today?</content>
</message>
</messages>"""
    
    user_prompt = f"""
Here is the conversation history:
{conversation}

Please return the indices of the messages where every time a new human agent comes on the line.
"""
    
    system_prompt = get_human_transfer_detection_audit_prompt()

    num_iterations = 50
    batch_size = 10
    
    for batch_num in range(0, num_iterations, batch_size):
        batch_end = min(batch_num + batch_size, num_iterations)
        print(f"\n--- Processing Batch {batch_num//batch_size + 1} (iterations {batch_num+1}-{batch_end}) ---")
        
        tasks = [
            call_and_verify(
                openai_client,
                system_prompt,
                user_prompt,
                response_format,
                i + 1,
                num_iterations,
            )
            for i in range(batch_num, batch_end)
        ]
        
        await asyncio.gather(*tasks)
    
    print(f"\nAll {num_iterations} iterations passed!")

