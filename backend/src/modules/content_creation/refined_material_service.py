"""
Refined Material Service

This module handles the extraction of structured, refined material from unstructured content.
This service can be used across different content creation workflows, not just for MCQs.
"""

from datetime import datetime
from typing import Any
import uuid

from src.core.llm_client import LLMClient
from src.core.prompt_base import PromptContext
from src.data_structures import RefinedMaterialResult

from .models import RefinedMaterialResponse
from .prompts.refined_material_extraction import RefinedMaterialExtractionPrompt


class RefinedMaterialService:
    """Service for extracting structured material from unstructured content"""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client
        self.refined_material_prompt = RefinedMaterialExtractionPrompt()

    async def extract_refined_material(
        self,
        source_material: str,
        domain: str = "",
        user_level: str = "intermediate",
        context: PromptContext | None = None,
    ) -> RefinedMaterialResponse:
        """
        Extract refined material from unstructured content

        Args:
            source_material: Unstructured text content
            domain: Subject domain (optional)
            user_level: Target user level (beginner, intermediate, advanced)
            context: Optional prompt context

        Returns:
            RefinedMaterialResponse object containing structured material with topics, learning objectives, etc.
        """
        if context is None:
            context = PromptContext()

        messages = self.refined_material_prompt.generate_prompt(
            context=context, source_material=source_material, domain=domain, user_level=user_level
        )

        # Use instructor to get structured refined material response
        refined_response = await self.llm_client.generate_structured_object(messages, RefinedMaterialResponse)

        return refined_response

    def save_refined_material_as_component(
        self, topic_id: str, refined_material: dict[str, Any], generation_prompt: str, raw_llm_response: str
    ) -> RefinedMaterialResult:
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
