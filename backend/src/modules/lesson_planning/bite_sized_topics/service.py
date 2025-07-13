"""
Bite-sized Topics Service

This module provides services for creating bite-sized topic content.
"""

from typing import Dict, List, Optional, Any
import logging
import re

from core import ModuleService, ServiceConfig, LLMClient
from core.prompt_base import create_default_context
from .prompts import LessonContentPrompt, DidacticSnippetPrompt, GlossaryPrompt, SocraticDialoguePrompt


class BiteSizedTopicError(Exception):
    """Exception for bite-sized topic errors"""
    pass


class BiteSizedTopicService(ModuleService):
    """Service for creating bite-sized topic content"""

    def __init__(self, config: ServiceConfig, llm_client: LLMClient):
        super().__init__(config, llm_client)
        self.prompts = {
            'lesson_content': LessonContentPrompt(),
            'didactic_snippet': DidacticSnippetPrompt(),
            'glossary': GlossaryPrompt(),
            'socratic_dialogue': SocraticDialoguePrompt(),
            # Future prompts will be added here
        }

    async def create_lesson_content(
        self,
        topic_title: str,
        topic_description: str,
        learning_objectives: List[str],
        user_level: str = "beginner",
        previous_topics: Optional[List[str]] = None,
        user_performance: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate lesson content for a specific topic.

        Args:
            topic_title: Title of the topic
            topic_description: Description of the topic
            learning_objectives: List of learning objectives
            user_level: User's skill level
            previous_topics: Previously covered topics
            user_performance: User's previous performance data

        Returns:
            Generated lesson content in markdown format

        Raises:
            BiteSizedTopicError: If content generation fails
        """
        try:
            # Check cache first
            cache_key = f"lesson_{hash(topic_title + topic_description + user_level)}"

            context = create_default_context(
                user_level=user_level,
                time_constraint=15,
                previous_performance=user_performance or {}
            )

            messages = self.prompts['lesson_content'].generate_prompt(
                context,
                topic_title=topic_title,
                topic_description=topic_description,
                learning_objectives=learning_objectives,
                previous_topics=previous_topics or []
            )

            response = await self.llm_client.generate_response(messages)
            content = response.content

            self.logger.info(f"Generated lesson content for '{topic_title}' ({len(content)} characters)")
            return content

        except Exception as e:
            self.logger.error(f"Failed to generate lesson content: {e}")
            raise BiteSizedTopicError(f"Failed to generate lesson content: {e}")

    async def create_didactic_snippet(
        self,
        topic_title: str,
        key_concept: str,
        user_level: str = "beginner",
        concept_context: Optional[str] = None,
        learning_objectives: Optional[List[str]] = None,
        previous_topics: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Create a didactic snippet for a specific concept.

        Args:
            topic_title: Title of the topic
            key_concept: Key concept to explain
            user_level: User's skill level
            concept_context: Additional context about the concept
            learning_objectives: Learning objectives for the concept
            previous_topics: Previously covered topics

        Returns:
            Dictionary with 'title' and 'snippet' keys

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=5  # Shorter for snippets
            )

            messages = self.prompts['didactic_snippet'].generate_prompt(
                context,
                topic_title=topic_title,
                key_concept=key_concept,
                concept_context=concept_context or "",
                learning_objectives=learning_objectives or [],
                previous_topics=previous_topics or []
            )

            response = await self.llm_client.generate_response(messages)

            # Parse the structured output
            parsed_snippet = self._parse_didactic_snippet(response.content)

            self.logger.info(f"Generated didactic snippet for '{key_concept}': {parsed_snippet['title']}")
            return parsed_snippet

        except Exception as e:
            self.logger.error(f"Failed to generate didactic snippet: {e}")
            raise BiteSizedTopicError(f"Failed to generate didactic snippet: {e}")

    def _parse_didactic_snippet(self, content: str) -> Dict[str, str]:
        """
        Parse the structured output from the didactic snippet prompt.

        Args:
            content: Raw LLM output containing title and snippet

        Returns:
            Dictionary with 'title' and 'snippet' keys

        Raises:
            BiteSizedTopicError: If parsing fails
        """
        try:
            # Remove code block markers if present
            content = content.strip()
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]

            # Split by lines and find title and snippet
            lines = content.strip().split('\n')
            title = ""
            snippet = ""

            for line in lines:
                if line.startswith('Title:'):
                    title = line[6:].strip()
                elif line.startswith('Snippet:'):
                    snippet = line[8:].strip()

            # If not found in expected format, try to extract from content
            if not title or not snippet:
                # Look for Title: and Snippet: in the content
                title_match = re.search(r'Title:\s*(.+)', content)
                snippet_match = re.search(r'Snippet:\s*(.+)', content, re.DOTALL)

                if title_match:
                    title = title_match.group(1).strip()
                if snippet_match:
                    snippet = snippet_match.group(1).strip()

            # Fallback: if still not found, use the entire content as snippet
            if not title:
                title = "Didactic Snippet"
            if not snippet:
                snippet = content.strip()

            return {
                'title': title,
                'snippet': snippet
            }

        except Exception as e:
            self.logger.error(f"Failed to parse didactic snippet: {e}")
            # Return a fallback structure
            return {
                'title': "Didactic Snippet",
                'snippet': content.strip()
            }

    async def create_glossary(
        self,
        topic_title: str,
        concepts: List[str],
        user_level: str = "beginner",
        lesson_context: Optional[str] = None,
        learning_objectives: Optional[List[str]] = None,
        previous_topics: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Create a glossary of concepts for a topic.

        Args:
            topic_title: Title of the topic
            concepts: List of concepts to explain
            user_level: User's skill level
            lesson_context: Additional context about the lesson
            learning_objectives: Learning objectives for the lesson
            previous_topics: Previously covered topics

        Returns:
            Dictionary mapping concepts to teaching-style explanations

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=10
            )

            messages = self.prompts['glossary'].generate_prompt(
                context,
                topic_title=topic_title,
                concepts=concepts,
                lesson_context=lesson_context or "",
                learning_objectives=learning_objectives or [],
                previous_topics=previous_topics or []
            )

            response = await self.llm_client.generate_response(messages)

            # Parse the structured output
            parsed_glossary = self._parse_glossary(response.content)

            self.logger.info(f"Generated glossary for '{topic_title}' with {len(parsed_glossary)} concepts")
            return parsed_glossary

        except Exception as e:
            self.logger.error(f"Failed to generate glossary: {e}")
            raise BiteSizedTopicError(f"Failed to generate glossary: {e}")

    def _parse_glossary(self, content: str) -> Dict[str, str]:
        """
        Parse the structured output from the glossary prompt.

        Args:
            content: Raw LLM output containing concept and explanation pairs

        Returns:
            Dictionary mapping concepts to explanations

        Raises:
            BiteSizedTopicError: If parsing fails
        """
        try:
            # Remove code block markers if present
            content = content.strip()
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]

            glossary = {}

            # Split by double newlines to separate entries
            entries = content.split('\n\n')

            for entry in entries:
                entry = entry.strip()
                if not entry:
                    continue

                # Look for Concept: and Explanation: patterns
                concept_match = re.search(r'Concept:\s*(.+?)(?=\n|$)', entry)
                explanation_match = re.search(r'Explanation:\s*(.+)', entry, re.DOTALL)

                if concept_match and explanation_match:
                    concept = concept_match.group(1).strip()
                    explanation = explanation_match.group(1).strip()

                    # Clean up the explanation (remove extra whitespace)
                    explanation = re.sub(r'\s+', ' ', explanation).strip()

                    glossary[concept] = explanation

            # If no entries found, try alternate parsing
            if not glossary:
                # Try to find entries by looking for lines that start with "Concept:"
                lines = content.split('\n')
                current_concept = None
                current_explanation = []

                for line in lines:
                    line = line.strip()
                    if line.startswith('Concept:'):
                        # Save previous entry if exists
                        if current_concept and current_explanation:
                            glossary[current_concept] = ' '.join(current_explanation)

                        # Start new entry
                        current_concept = line[8:].strip()
                        current_explanation = []
                    elif line.startswith('Explanation:'):
                        current_explanation = [line[12:].strip()]
                    elif current_concept and line:
                        current_explanation.append(line)

                # Save last entry
                if current_concept and current_explanation:
                    glossary[current_concept] = ' '.join(current_explanation)

            return glossary

        except Exception as e:
            self.logger.error(f"Failed to parse glossary: {e}")
            # Return empty glossary on parse failure
            return {}

    async def create_socratic_dialogue(
        self,
        topic_title: str,
        core_concept: str,
        user_level: str = "beginner",
        learning_objectives: Optional[List[str]] = None,
        previous_topics: Optional[List[str]] = None,
        target_insights: Optional[List[str]] = None,
        common_misconceptions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create a set of Socratic dialogue exercises for a concept.

        Args:
            topic_title: Title of the topic
            core_concept: Core concept to explore through dialogue
            user_level: User's skill level
            learning_objectives: Learning objectives for the concept
            previous_topics: Previously covered topics
            target_insights: Key insights the learner should discover
            common_misconceptions: Common misconceptions to address

        Returns:
            List of dialogue dictionaries with metadata

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=20  # Longer for interactive dialogues
            )

            messages = self.prompts['socratic_dialogue'].generate_prompt(
                context,
                topic_title=topic_title,
                core_concept=core_concept,
                learning_objectives=learning_objectives or [],
                previous_topics=previous_topics or [],
                target_insights=target_insights or [],
                common_misconceptions=common_misconceptions or []
            )

            response = await self.llm_client.generate_response(messages)

            # Parse the structured output
            parsed_dialogues = self._parse_socratic_dialogues(response.content)

            self.logger.info(f"Generated {len(parsed_dialogues)} Socratic dialogues for '{core_concept}'")
            return parsed_dialogues

        except Exception as e:
            self.logger.error(f"Failed to generate Socratic dialogues: {e}")
            raise BiteSizedTopicError(f"Failed to generate Socratic dialogues: {e}")

    def _parse_socratic_dialogues(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse the structured output from the Socratic dialogue prompt.

        Args:
            content: Raw LLM output containing multiple dialogue entries

        Returns:
            List of dialogue dictionaries with metadata

        Raises:
            BiteSizedTopicError: If parsing fails
        """
        try:
            # Remove code block markers if present
            content = content.strip()
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]

            dialogues = []

            # Split by "Dialogue" followed by a number
            dialogue_sections = re.split(r'\n\s*Dialogue\s+\d+\s*\n', content)

            # Remove empty first section if it exists
            if dialogue_sections and not dialogue_sections[0].strip():
                dialogue_sections = dialogue_sections[1:]

            for section in dialogue_sections:
                section = section.strip()
                if not section:
                    continue

                dialogue = {}

                # Extract each field using regex
                fields = {
                    'concept': r'Concept:\s*(.+?)(?=\n\s*\w+:|$)',
                    'dialogue_objective': r'Dialogue Objective:\s*(.+?)(?=\n\s*\w+:|$)',
                    'starting_prompt': r'Starting Prompt:\s*(.+?)(?=\n\s*\w+:|$)',
                    'dialogue_style': r'Dialogue Style:\s*(.+?)(?=\n\s*\w+:|$)',
                    'hints_and_scaffolding': r'Hints and Scaffolding:\s*(.+?)(?=\n\s*\w+:|$)',
                    'exit_criteria': r'Exit Criteria:\s*(.+?)(?=\n\s*\w+:|$)',
                    'difficulty': r'Difficulty:\s*(\d+)',
                    'tags': r'Tags:\s*(.+?)(?=\n\s*\w+:|$)'
                }

                for field, pattern in fields.items():
                    match = re.search(pattern, section, re.DOTALL | re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        # Clean up multi-line values
                        value = re.sub(r'\s+', ' ', value).strip()

                        # Special handling for difficulty (convert to int)
                        if field == 'difficulty':
                            try:
                                dialogue[field] = int(value)
                            except ValueError:
                                dialogue[field] = 3  # Default difficulty
                        else:
                            dialogue[field] = value
                    else:
                        # Provide defaults for missing fields
                        if field == 'difficulty':
                            dialogue[field] = 3
                        else:
                            dialogue[field] = ""

                # Only add dialogue if it has essential fields
                if dialogue.get('concept') and dialogue.get('starting_prompt'):
                    dialogues.append(dialogue)

            return dialogues

        except Exception as e:
            self.logger.error(f"Failed to parse Socratic dialogues: {e}")
            # Return empty list on parse failure
            return []

    async def validate_content(self, content: str) -> Dict[str, Any]:
        """
        Validate generated content for quality and structure.

        Args:
            content: Content to validate

        Returns:
            Validation results

        Raises:
            BiteSizedTopicError: If validation fails
        """
        try:
            issues = []

            # Basic content checks
            if not content or len(content.strip()) < 100:
                issues.append("Content too short")

            if len(content) > 5000:
                issues.append("Content too long for 15-minute lesson")

            # Check for markdown formatting
            if not any(marker in content for marker in ['#', '**', '*', '-', '1.']):
                issues.append("Content lacks proper formatting")

            # Check for interactive elements
            if not any(marker in content for marker in ['?', 'exercise', 'question', 'think', 'consider']):
                issues.append("Content lacks interactive elements")

            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "word_count": len(content.split()),
                "estimated_reading_time": len(content.split()) / 200  # Words per minute
            }

        except Exception as e:
            self.logger.error(f"Failed to validate content: {e}")
            raise BiteSizedTopicError(f"Failed to validate content: {e}")