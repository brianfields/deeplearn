"""
Content Creator Module - Service Layer

AI-powered content generation services.
Uses LLM services to create educational content and stores it via content module.
"""

from typing import Any
import uuid

from pydantic import BaseModel

from modules.content.public import ComponentCreate, ContentProvider, TopicCreate
from modules.llm_services.public import LLMMessage, LLMServicesProvider


# DTOs
class CreateTopicRequest(BaseModel):
    """Request to create a topic from source material."""

    title: str
    core_concept: str
    source_material: str
    user_level: str = "intermediate"
    domain: str = "General"


class CreateComponentRequest(BaseModel):
    """Request to create a component for an existing topic."""

    component_type: str
    learning_objective: str


class TopicCreationResult(BaseModel):
    """Result of topic creation with component count."""

    topic_id: str
    title: str
    components_created: int


class ContentCreatorService:
    """Service for AI-powered content creation."""

    def __init__(self, content: ContentProvider, llm: LLMServicesProvider):
        """Initialize with content storage and LLM services."""
        self.content = content
        self.llm = llm

    async def create_topic_from_source_material(self, request: CreateTopicRequest) -> TopicCreationResult:
        """
        Create a complete topic with AI-generated content from source material.

        This method:
        1. Uses LLM to extract structured content from source material
        2. Creates the topic in the content module
        3. Generates and saves components (didactic snippet, glossary, MCQs)
        4. Returns summary of what was created
        """
        topic_id = str(uuid.uuid4())

        # Extract structured content using LLM
        extracted_content = await self._extract_topic_content(request.title, request.core_concept, request.source_material, request.user_level, request.domain)

        # Save topic to content module
        topic_data = TopicCreate(
            id=topic_id,
            title=request.title,
            core_concept=request.core_concept,
            user_level=request.user_level,
            learning_objectives=extracted_content["learning_objectives"],
            key_concepts=extracted_content["key_concepts"],
            source_material=request.source_material,
            source_domain=request.domain,
            source_level=request.user_level,
            refined_material=extracted_content.get("refined_material", {}),
        )

        saved_topic = self.content.save_topic(topic_data)

        # Generate and save components
        components_created = 0

        # Create didactic snippet
        if "didactic_snippet" in extracted_content:
            component_data = ComponentCreate(id=str(uuid.uuid4()), topic_id=topic_id, component_type="didactic_snippet", title=f"Overview: {request.title}", content=extracted_content["didactic_snippet"])
            self.content.save_component(component_data)
            components_created += 1

        # Create glossary
        if "glossary" in extracted_content:
            component_data = ComponentCreate(id=str(uuid.uuid4()), topic_id=topic_id, component_type="glossary", title=f"Glossary: {request.title}", content=extracted_content["glossary"])
            self.content.save_component(component_data)
            components_created += 1

        # Create MCQs
        for i, mcq in enumerate(extracted_content.get("mcqs", [])):
            component_data = ComponentCreate(id=str(uuid.uuid4()), topic_id=topic_id, component_type="mcq", title=f"Question {i + 1}: {mcq.get('title', 'MCQ')}", content=mcq)
            self.content.save_component(component_data)
            components_created += 1

        return TopicCreationResult(topic_id=topic_id, title=request.title, components_created=components_created)

    async def generate_component(self, topic_id: str, request: CreateComponentRequest) -> str:
        """
        Generate a single component for an existing topic.

        Args:
            topic_id: ID of existing topic
            request: Component creation request

        Returns:
            ID of created component

        Raises:
            ValueError: If topic doesn't exist or component type unsupported
        """
        # Verify topic exists
        topic = self.content.get_topic(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")

        component_id = str(uuid.uuid4())

        # Generate component content using LLM
        if request.component_type == "mcq":
            content = await self._generate_mcq(topic, request.learning_objective)
        elif request.component_type == "didactic_snippet":
            content = await self._generate_didactic_snippet(topic, request.learning_objective)
        elif request.component_type == "glossary":
            content = await self._generate_glossary(topic)
        else:
            raise ValueError(f"Unsupported component type: {request.component_type}")

        # Save component
        component_data = ComponentCreate(id=component_id, topic_id=topic_id, component_type=request.component_type, title=f"{request.component_type.replace('_', ' ').title()}", content=content, learning_objective=request.learning_objective)

        self.content.save_component(component_data)
        return component_id

    async def _extract_topic_content(self, title: str, core_concept: str, source_material: str, user_level: str, domain: str) -> dict[str, Any]:
        """
        Use LLM to extract structured content from source material.

        This is a simplified version - in a full implementation, this would use
        the existing MaterialExtractionService and MCQGenerationService logic.
        """
        prompt = f"""
        Extract structured learning content from the following material:

        Title: {title}
        Core Concept: {core_concept}
        User Level: {user_level}
        Domain: {domain}

        Source Material:
        {source_material}

        Generate a JSON response with:
        1. learning_objectives: Array of 3-5 specific learning goals
        2. key_concepts: Array of important terms/ideas
        3. refined_material: Structured overview object
        4. didactic_snippet: Object with explanation and key_points
        5. glossary: Object with terms array (term, definition)
        6. mcqs: Array of MCQ objects with question, options, correct_answer

        Format as valid JSON.
        """

        messages = [LLMMessage(role="user", content=prompt)]
        response, request_id = await self.llm.generate_response(messages)
        return self._parse_llm_response(response.content)

    async def _generate_mcq(self, topic, learning_objective: str) -> dict[str, Any]:
        """Generate MCQ using LLM based on topic and learning objective."""
        prompt = f"""
        Create a multiple choice question for this topic:

        Topic: {topic.title}
        Core Concept: {topic.core_concept}
        Learning Objective: {learning_objective}
        User Level: {topic.user_level}

        Generate a JSON object with:
        - question: The question text
        - options: Array of 4 answer options
        - correct_answer: Index of correct option (0-3)
        - explanation: Why the correct answer is right
        """

        messages = [LLMMessage(role="user", content=prompt)]
        response, request_id = await self.llm.generate_response(messages)
        return self._parse_llm_response(response.content)

    async def _generate_didactic_snippet(self, topic, learning_objective: str) -> dict[str, Any]:
        """Generate didactic snippet using LLM."""
        prompt = f"""
        Create an educational explanation for this topic:

        Topic: {topic.title}
        Core Concept: {topic.core_concept}
        Learning Objective: {learning_objective}
        User Level: {topic.user_level}

        Generate a JSON object with:
        - explanation: Clear, educational explanation
        - key_points: Array of 3-5 key takeaways
        """

        messages = [LLMMessage(role="user", content=prompt)]
        response, request_id = await self.llm.generate_response(messages)
        return self._parse_llm_response(response.content)

    async def _generate_glossary(self, topic) -> dict[str, Any]:
        """Generate glossary using LLM."""
        prompt = f"""
        Create a glossary for this topic:

        Topic: {topic.title}
        Core Concept: {topic.core_concept}
        Key Concepts: {", ".join(topic.key_concepts)}
        User Level: {topic.user_level}

        Generate a JSON object with:
        - terms: Array of objects with 'term' and 'definition' fields
        """

        messages = [LLMMessage(role="user", content=prompt)]
        response, request_id = await self.llm.generate_response(messages)
        return self._parse_llm_response(response.content)

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """
        Parse LLM response into structured format.

        In a full implementation, this would handle JSON parsing,
        validation, and error handling properly.
        """
        import json

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback for malformed JSON
            return {
                "learning_objectives": ["Learn about the topic"],
                "key_concepts": ["Key concept"],
                "refined_material": {"overview": "Generated content"},
                "didactic_snippet": {"explanation": "Educational content", "key_points": ["Point 1"]},
                "glossary": {"terms": [{"term": "Term", "definition": "Definition"}]},
                "mcqs": [],
            }
