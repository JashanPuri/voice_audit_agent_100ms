import os
from typing import List, Dict, Optional, Any
from openai import AsyncOpenAI
from openai.types.responses import ResponseInputParam


class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Please provide it as a parameter "
                "or set the OPENAI_API_KEY environment variable."
            )
        
        self.client: AsyncOpenAI = AsyncOpenAI(api_key=self.api_key)
        self.model = model
    
    async def generate_response(
        self,
        system_prompt: str,
        messages: ResponseInputParam,
        temperature: float = 0,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        kwargs = {
            "model": self.model,
            "instructions": system_prompt,
            "input": messages,
            "temperature": temperature,
        }
        
        if response_format is not None:
            kwargs["text"] = {"format": response_format}
        
        response = await self.client.responses.create(**kwargs)
        
        return response.output_text

