"""
Refined Material Service

This module handles the extraction of structured, refined material from unstructured content.
This service can be used across different content creation workflows, not just for MCQs.
"""

import json
import uuid
from datetime import datetime
from typing import Any

from src.core.llm_client import LLMClient
from src.core.prompt_base import PromptContext
from src.data_structures import RefinedMaterialResult

from .prompts.refined_material_extraction import RefinedMaterialExtractionPrompt


class RefinedMaterialService:
    """Service for extracting structured material from unstructured content"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.refined_material_prompt = RefinedMaterialExtractionPrompt()

    async def extract_refined_material(self, source_material: str, domain: str = "", user_level: str = "intermediate", context: PromptContext | None = None) -> dict[str, Any]:
        """
        Extract refined material from unstructured content

        Args:
            source_material: Unstructured text content
            domain: Subject domain (optional)
            user_level: Target user level (beginner, intermediate, advanced)
            context: Optional prompt context

        Returns:
            Dictionary containing structured material with topics, learning objectives, etc.
        """
        if context is None:
            context = PromptContext()

        messages = self.refined_material_prompt.generate_prompt(context=context, source_material=source_material, domain=domain, user_level=user_level)

        response = await self.llm_client.generate_response(messages)

        try:
            # Clean and extract JSON from response
            content = response.content.strip()

            # Try to find JSON in the response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                refined_material = json.loads(json_content)
                return refined_material
            else:
                # If no JSON found, try parsing the entire response
                refined_material = json.loads(content)
                return refined_material

        except json.JSONDecodeError as e:
            # Log the actual response for debugging
            print(f"Raw LLM Response: {response.content}")
            raise ValueError(f"Failed to parse refined material JSON: {e}") from e

    def save_refined_material_as_component(self, topic_id: str, refined_material: dict[str, Any], generation_prompt: str, raw_llm_response: str) -> RefinedMaterialResult:
        """Save refined material as a bite-sized component"""

        component_id = str(uuid.uuid4())
        now = datetime.utcnow()

        result = RefinedMaterialResult(
            id=component_id,
            topic_id=topic_id,
            component_type="refined_material",
            title="Refined Material",
            content=refined_material,
            generation_prompt=generation_prompt,
            raw_llm_response=raw_llm_response,
            created_at=now,
            updated_at=now,
        )

        return result
