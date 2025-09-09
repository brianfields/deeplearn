"""Content creation flows using flow engine infrastructure."""

import logging
from typing import Any

from pydantic import BaseModel

from modules.flow_engine.public import BaseFlow

from .steps import ExtractTopicMetadataStep, GenerateDidacticSnippetStep, GenerateGlossaryStep, GenerateMCQStep

logger = logging.getLogger(__name__)


class TopicCreationFlow(BaseFlow):
    """Multi-step flow that creates a complete topic with all components."""

    flow_name = "topic_creation"

    class Inputs(BaseModel):
        title: str
        core_concept: str
        source_material: str
        user_level: str = "intermediate"
        domain: str = "General"

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info(f"📚 Topic Creation Flow - Processing: {inputs.get('title', 'Unknown Topic')}")

        # Step 1: Extract topic metadata (learning objectives, key concepts)
        logger.info("📋 Step 1: Extracting topic metadata...")
        metadata_result = await ExtractTopicMetadataStep().execute(inputs)
        metadata = metadata_result.output_content
        logger.info(f"✅ Extracted {len(metadata.learning_objectives)} learning objectives and {len(metadata.key_concepts)} key concepts")

        # Prepare common inputs for component generation
        component_inputs = {"topic_title": inputs["title"], "core_concept": inputs["core_concept"], "user_level": inputs["user_level"], "key_concepts": metadata.key_concepts}

        # Step 2: Generate didactic snippet
        logger.info("📝 Step 2: Generating didactic snippet...")
        didactic_result = await GenerateDidacticSnippetStep().execute({**component_inputs, "learning_objective": "Understand the core concept and key principles"})

        # Step 3: Generate glossary
        logger.info("📖 Step 3: Generating glossary...")
        glossary_result = await GenerateGlossaryStep().execute(component_inputs)

        # Step 4: Generate multiple MCQs (one for each learning objective)
        logger.info(f"❓ Step 4: Generating {len(metadata.learning_objectives)} MCQs...")
        mcq_results = []
        for i, learning_objective in enumerate(metadata.learning_objectives, 1):
            logger.debug(f"Generating MCQ {i}/{len(metadata.learning_objectives)}: {learning_objective[:50]}...")
            mcq_result = await GenerateMCQStep().execute({**component_inputs, "learning_objective": learning_objective})
            mcq_results.append(mcq_result)

        # Return dictionary (as required by BaseFlow.execute())
        # Flow engine automatically tracks all metadata in database
        return {
            "learning_objectives": metadata.learning_objectives,
            "key_concepts": metadata.key_concepts,
            "refined_material": metadata.refined_material,
            "didactic_snippet": didactic_result.output_content.model_dump(),
            "glossary": glossary_result.output_content.model_dump(),
            "mcqs": [mcq.output_content.model_dump() for mcq in mcq_results],
        }
