import asyncio
import json
from typing import Type, Optional
from pydantic import BaseModel, ValidationError
from google.genai import Client
from google.genai.types import GenerateContentConfig
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings


class GeminiClient:
    """Async client for Google Gemini AI."""
    
    def __init__(self, api_key: str):
        self.client = Client(api_key=api_key)
        self.model = 'gemini-2.5-flash'
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_structured(
        self, 
        prompt: str, 
        response_schema: Type[BaseModel],
        temperature: float = 0.3
    ) -> BaseModel:
        """
        Generate structured response from Gemini.
        
        Args:
            prompt: The prompt text
            response_schema: Pydantic model for response validation
            temperature: Creativity level (0-1)
            
        Returns:
            Validated response model instance
        """
        # Convert Pydantic model to JSON schema for Gemini
        schema_dict = response_schema.model_json_schema()
        
        # Generate response using google.genai API with response_schema
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=GenerateContentConfig(
                    temperature=temperature,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=4096,
                    response_mime_type='application/json',
                    response_schema=schema_dict
                )
            )
        )
        
        # Parse and validate
        try:
            text = response.text
            # Extract JSON if wrapped in markdown
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            data = json.loads(text)
            return response_schema(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Failed to parse response: {e}")
            print(f"Raw response: {response.text}")
            raise ValueError(f"Invalid response format: {e}")


# Global client instance
_llm_client: Optional[GeminiClient] = None


async def get_llm_client() -> GeminiClient:
    """Get or create LLM client."""
    global _llm_client
    if _llm_client is None:
        settings = get_settings()
        _llm_client = GeminiClient(settings.GEMINI_API_KEY)
    return _llm_client
