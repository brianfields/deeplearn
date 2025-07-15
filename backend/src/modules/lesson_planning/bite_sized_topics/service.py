"""
Bite-sized Topics Service

This module provides services for creating bite-sized topic content.
"""

from typing import Dict, List, Optional, Any
import logging
import re

from core import ModuleService, ServiceConfig, LLMClient
from core.prompt_base import create_default_context
from .prompts import LessonContentPrompt, DidacticSnippetPrompt, GlossaryPrompt, SocraticDialoguePrompt, ShortAnswerQuestionsPrompt, MultipleChoiceQuestionsPrompt, PostTopicQuizPrompt


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
            'short_answer_questions': ShortAnswerQuestionsPrompt(),
            'multiple_choice_questions': MultipleChoiceQuestionsPrompt(),
            'post_topic_quiz': PostTopicQuizPrompt(),
            # Future prompts will be added here
        }

    def _format_messages_for_storage(self, messages: List[Any]) -> str:
        """
        Format LLM messages for storage in database.

        Args:
            messages: List of LLM messages

        Returns:
            String representation of messages suitable for storage
        """
        formatted_messages = []
        for msg in messages:
            role = getattr(msg, 'role', 'unknown')
            content = getattr(msg, 'content', '')
            formatted_messages.append(f"[{role}]: {content}")
        return "\n\n".join(formatted_messages)

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
    ) -> Dict[str, Any]:
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

            # Add generation metadata separately (not in content)
            parsed_snippet['_generation_metadata'] = {
                'generation_prompt': self._format_messages_for_storage(messages),
                'raw_llm_response': response.content
            }

            self.logger.info(f"Generated didactic snippet for '{key_concept}': {parsed_snippet['title']}")
            return parsed_snippet

        except Exception as e:
            self.logger.error(f"Failed to generate didactic snippet: {e}")
            raise BiteSizedTopicError(f"Failed to generate didactic snippet: {e}")

    def _parse_didactic_snippet(self, content: str) -> Dict[str, Any]:
        """
        Parse the structured output from the didactic snippet prompt.

        Args:
            content: Raw LLM output containing title and snippet

        Returns:
            Dictionary with consolidated content including title and all snippet data

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

            # Return consolidated content structure
            return {
                'title': title,
                'snippet': snippet,
                'type': 'didactic_snippet',
                'difficulty': 2  # Default difficulty for didactic snippets
            }

        except Exception as e:
            self.logger.error(f"Failed to parse didactic snippet: {e}")
            # Return a fallback structure
            return {
                'title': "Didactic Snippet",
                'snippet': content.strip(),
                'type': 'didactic_snippet',
                'difficulty': 2
            }

    async def create_glossary(
        self,
        topic_title: str,
        concepts: List[str],
        user_level: str = "beginner",
        lesson_context: Optional[str] = None,
        learning_objectives: Optional[List[str]] = None,
        previous_topics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create a glossary of concepts for a topic.

        Args:
            topic_title: Title of the topic
            concepts: List of concepts to explain (if empty, LLM will identify concepts)
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

            # If no concepts provided, let LLM identify meaningful concepts
            if not concepts:
                concepts = [f"IDENTIFY_CONCEPTS_FROM:{topic_title}"]

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

            # Add generation metadata to each glossary entry
            generation_metadata = {
                'generation_prompt': self._format_messages_for_storage(messages),
                'raw_llm_response': response.content
            }
            for entry in parsed_glossary:
                entry['_generation_metadata'] = generation_metadata

            self.logger.info(f"Generated glossary for '{topic_title}' with {len(parsed_glossary)} concepts")
            return parsed_glossary

        except Exception as e:
            self.logger.error(f"Failed to generate glossary: {e}")
            raise BiteSizedTopicError(f"Failed to generate glossary: {e}")

    def _parse_glossary(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse the structured output from the glossary prompt.

        Args:
            content: Raw LLM output containing concept and explanation pairs

        Returns:
            List of glossary entry dictionaries with consolidated content

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

            glossary_entries = []

            # Split by double newlines to separate entries
            entries = content.split('\n\n')

            for i, entry in enumerate(entries, 1):
                entry = entry.strip()
                if not entry:
                    continue

                glossary_entry = {
                    'type': 'glossary_entry',
                    'number': i
                }

                # Look for Concept:, Title:, and Explanation: patterns
                concept_match = re.search(r'Concept:\s*(.+?)(?=\n|$)', entry)
                title_match = re.search(r'Title:\s*(.+?)(?=\n|$)', entry)
                explanation_match = re.search(r'Explanation:\s*(.+)', entry, re.DOTALL)

                if concept_match:
                    glossary_entry['concept'] = concept_match.group(1).strip()

                if title_match:
                    glossary_entry['title'] = title_match.group(1).strip()
                else:
                    glossary_entry['title'] = f"Glossary: {glossary_entry.get('concept', f'Term {i}')}"

                if explanation_match:
                    explanation = explanation_match.group(1).strip()
                    # Clean up the explanation (remove extra whitespace)
                    explanation = re.sub(r'\s+', ' ', explanation).strip()
                    glossary_entry['explanation'] = explanation

                # Add metadata
                glossary_entry['difficulty'] = 2  # Default difficulty for glossary entries

                # Only add if we have essential fields
                if glossary_entry.get('concept') and glossary_entry.get('explanation'):
                    glossary_entries.append(glossary_entry)

            # If no entries found, try alternate parsing
            if not glossary_entries:
                # Try to find entries by looking for lines that start with "Concept:"
                lines = content.split('\n')
                current_concept = None
                current_title = None
                current_explanation = []

                for line in lines:
                    line = line.strip()
                    if line.startswith('Concept:'):
                        # Save previous entry if exists
                        if current_concept and current_explanation:
                            glossary_entries.append({
                                'type': 'glossary_entry',
                                'number': len(glossary_entries) + 1,
                                'concept': current_concept,
                                'title': current_title or f"Glossary: {current_concept}",
                                'explanation': ' '.join(current_explanation),
                                'difficulty': 2
                            })

                        # Start new entry
                        current_concept = line[8:].strip()
                        current_title = None
                        current_explanation = []
                    elif line.startswith('Title:'):
                        current_title = line[6:].strip()
                    elif line.startswith('Explanation:'):
                        current_explanation = [line[12:].strip()]
                    elif current_concept and line:
                        current_explanation.append(line)

                # Save last entry
                if current_concept and current_explanation:
                    glossary_entries.append({
                        'type': 'glossary_entry',
                        'number': len(glossary_entries) + 1,
                        'concept': current_concept,
                        'title': current_title or f"Glossary: {current_concept}",
                        'explanation': ' '.join(current_explanation),
                        'difficulty': 2
                    })

            return glossary_entries

        except Exception as e:
            self.logger.error(f"Failed to parse glossary: {e}")
            # Return empty list on parse failure
            return []

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

            # Add generation metadata to each dialogue
            generation_metadata = {
                'generation_prompt': self._format_messages_for_storage(messages),
                'raw_llm_response': response.content
            }
            for dialogue in parsed_dialogues:
                dialogue['_generation_metadata'] = generation_metadata

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
            List of dialogue dictionaries with consolidated content and metadata

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

            for i, section in enumerate(dialogue_sections, 1):
                section = section.strip()
                if not section:
                    continue

                dialogue = {
                    'type': 'socratic_dialogue',
                    'number': i
                }

                # Parse each field more carefully to handle malformed output
                field_patterns = {
                    'title': r'Title:\s*([^\n]+)',
                    'concept': r'Concept:\s*([^\n]+?)(?=\s+Dialogue\s+Objective:|$)',
                    'dialogue_objective': r'Dialogue\s+Objective:\s*([^\n]+?)(?=\s+Starting\s+Prompt:|$)',
                    'starting_prompt': r'Starting\s+Prompt:\s*([^\n]+?)(?=\s+Dialogue\s+Style:|$)',
                    'dialogue_style': r'Dialogue\s+Style:\s*([^\n]+?)(?=\s+Hints\s+and\s+Scaffolding:|$)',
                    'hints_and_scaffolding': r'Hints\s+and\s+Scaffolding:\s*([^\n]+?)(?=\s+Exit\s+Criteria:|$)',
                    'exit_criteria': r'Exit\s+Criteria:\s*([^\n]+?)(?=\s+Difficulty:|$)',
                    'difficulty': r'Difficulty:\s*(\d+)',
                    'tags': r'Tags:\s*([^\n]+)'
                }

                                # Try to extract from properly formatted lines first
                for field, pattern in field_patterns.items():
                    # Look for the field on its own line (proper format)
                    proper_match = re.search(f'\n{pattern}', section, re.IGNORECASE)

                    if proper_match:
                        value = proper_match.group(1).strip()
                    else:
                        # Fall back to the original regex for edge cases
                        field_title = field.replace("_", "\\s+").title()
                        fallback_pattern = f'{field_title}:\\s*(.+?)(?=\\n\\s*\\w+:|$)'
                        fallback_match = re.search(fallback_pattern, section, re.DOTALL | re.IGNORECASE)
                        if fallback_match:
                            value = fallback_match.group(1).strip()
                        else:
                            value = None

                    if value:
                        # Clean up multi-line values and remove embedded field names
                        value = re.sub(r'\s+', ' ', value).strip()

                        # Remove any embedded field names that might have been captured
                        value = re.sub(r'\s+(Title|Concept|Dialogue\s+Objective|Starting\s+Prompt|Dialogue\s+Style|Hints\s+and\s+Scaffolding|Exit\s+Criteria|Difficulty|Tags):\s*', '', value, flags=re.IGNORECASE)

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
                        elif field == 'title':
                            dialogue[field] = f"Socratic Dialogue {i}"
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

    async def create_short_answer_questions(
        self,
        topic_title: str,
        core_concept: str,
        user_level: str = "beginner",
        learning_objectives: Optional[List[str]] = None,
        previous_topics: Optional[List[str]] = None,
        key_aspects: Optional[List[str]] = None,
        avoid_overlap_with: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create a set of short answer questions for a concept.

        Args:
            topic_title: Title of the topic
            core_concept: Core concept to assess
            user_level: User's skill level
            learning_objectives: Learning objectives for the concept
            previous_topics: Previously covered topics
            key_aspects: Key aspects to cover in questions
            avoid_overlap_with: Topics/concepts to avoid overlapping with

        Returns:
            List of question dictionaries with metadata

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=15  # Standard time for assessment
            )

            messages = self.prompts['short_answer_questions'].generate_prompt(
                context,
                topic_title=topic_title,
                core_concept=core_concept,
                learning_objectives=learning_objectives or [],
                previous_topics=previous_topics or [],
                key_aspects=key_aspects or [],
                avoid_overlap_with=avoid_overlap_with or []
            )

            response = await self.llm_client.generate_response(messages)

            # Parse the structured output
            parsed_questions = self._parse_short_answer_questions(response.content)

            # Add generation metadata to each question
            generation_metadata = {
                'generation_prompt': self._format_messages_for_storage(messages),
                'raw_llm_response': response.content
            }
            for question in parsed_questions:
                question['_generation_metadata'] = generation_metadata

            self.logger.info(f"Generated {len(parsed_questions)} short answer questions for '{core_concept}'")
            return parsed_questions

        except Exception as e:
            self.logger.error(f"Failed to generate short answer questions: {e}")
            raise BiteSizedTopicError(f"Failed to generate short answer questions: {e}")

    def _parse_short_answer_questions(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse the structured output from the short answer questions prompt.

        Args:
            content: Raw LLM output containing multiple question entries

        Returns:
            List of question dictionaries with consolidated content and metadata

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

            questions = []

            # Split by "Question" followed by a number
            question_sections = re.split(r'\n\s*Question\s+\d+\s*\n', content)

            # Remove empty first section if it exists
            if question_sections and not question_sections[0].strip():
                question_sections = question_sections[1:]

            for i, section in enumerate(question_sections, 1):
                section = section.strip()
                if not section:
                    continue

                question_data = {
                    'type': 'short_answer_question',
                    'number': i
                }

                # Extract each field using regex
                fields = {
                    'title': r'Title:\s*(.+?)(?=\n\s*\w+:|$)',
                    'question': r'Question:\s*(.+?)(?=\n\s*\w+:|$)',
                    'purpose': r'Purpose:\s*(.+?)(?=\n\s*\w+:|$)',
                    'target_concept': r'Target Concept:\s*(.+?)(?=\n\s*\w+:|$)',
                    'expected_elements': r'Expected Elements of a Good Answer:\s*(.+?)(?=\n\s*\w+:|$)',
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
                                question_data[field] = int(value)
                            except ValueError:
                                question_data[field] = 3  # Default difficulty
                        else:
                            question_data[field] = value
                    else:
                        # Provide defaults for missing fields
                        if field == 'difficulty':
                            question_data[field] = 3
                        elif field == 'title':
                            question_data[field] = f"Short Answer Question {i}"
                        else:
                            question_data[field] = ""

                # Only add question if it has essential fields
                if question_data.get('question') and question_data.get('purpose'):
                    questions.append(question_data)

            return questions

        except Exception as e:
            self.logger.error(f"Failed to parse short answer questions: {e}")
            # Return empty list on parse failure
            return []

    async def create_multiple_choice_questions(
        self,
        topic_title: str,
        core_concept: str,
        user_level: str = "beginner",
        learning_objectives: Optional[List[str]] = None,
        previous_topics: Optional[List[str]] = None,
        key_aspects: Optional[List[str]] = None,
        common_misconceptions: Optional[List[str]] = None,
        avoid_overlap_with: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create a set of multiple choice questions for a concept.

        Args:
            topic_title: Title of the topic
            core_concept: Core concept to assess
            user_level: User's skill level
            learning_objectives: Learning objectives for the concept
            previous_topics: Previously covered topics
            key_aspects: Key aspects to cover in questions
            common_misconceptions: Common misconceptions to address
            avoid_overlap_with: Topics/concepts to avoid overlapping with

        Returns:
            List of MCQ dictionaries with metadata and justifications

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=15  # Standard time for assessment
            )

            messages = self.prompts['multiple_choice_questions'].generate_prompt(
                context,
                topic_title=topic_title,
                core_concept=core_concept,
                learning_objectives=learning_objectives or [],
                previous_topics=previous_topics or [],
                key_aspects=key_aspects or [],
                common_misconceptions=common_misconceptions or [],
                avoid_overlap_with=avoid_overlap_with or []
            )

            response = await self.llm_client.generate_response(messages)

            # Parse the structured output
            parsed_questions = self._parse_multiple_choice_questions(response.content)

            # Add generation metadata to each question
            generation_metadata = {
                'generation_prompt': self._format_messages_for_storage(messages),
                'raw_llm_response': response.content
            }
            for question in parsed_questions:
                question['_generation_metadata'] = generation_metadata

            self.logger.info(f"Generated {len(parsed_questions)} multiple choice questions for '{core_concept}'")
            return parsed_questions

        except Exception as e:
            self.logger.error(f"Failed to generate multiple choice questions: {e}")
            raise BiteSizedTopicError(f"Failed to generate multiple choice questions: {e}")

    def _parse_multiple_choice_questions(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse the structured output from the multiple choice questions prompt.

        Args:
            content: Raw LLM output containing multiple MCQ entries

        Returns:
            List of MCQ dictionaries with metadata and justifications

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

            questions = []

            # Split by "Question" followed by a number
            question_sections = re.split(r'\n\s*Question\s+\d+\s*\n', content)

            # Remove empty first section if it exists
            if question_sections and not question_sections[0].strip():
                question_sections = question_sections[1:]

            for i, section in enumerate(question_sections, 1):
                section = section.strip()
                if not section:
                    continue

                question_data = {
                    'type': 'multiple_choice_question',
                    'number': i
                }

                # Extract title
                title_match = re.search(r'Title:\s*(.+?)(?=\n\s*Question:)', section, re.DOTALL)
                if title_match:
                    question_data['title'] = title_match.group(1).strip()
                else:
                    question_data['title'] = f"Multiple Choice Question {i}"

                # Extract question stem
                question_match = re.search(r'Question:\s*(.+?)(?=\n\s*Choices:)', section, re.DOTALL)
                if question_match:
                    question_data['question'] = question_match.group(1).strip()

                # Extract choices
                choices_match = re.search(r'Choices:\s*(.+?)(?=\n\s*Correct Answer:)', section, re.DOTALL)
                if choices_match:
                    choices_text = choices_match.group(1).strip()
                    choices = {}

                    # Parse individual choices
                    choice_lines = choices_text.split('\n')
                    for line in choice_lines:
                        line = line.strip()
                        # Match pattern like "A. Some text" or "(D. Some text)"
                        choice_match = re.match(r'^\(?([A-D])\.\s*(.+)$', line)
                        if choice_match:
                            choice_letter = choice_match.group(1)
                            choice_text = choice_match.group(2).strip()
                            choices[choice_letter] = choice_text

                    question_data['choices'] = choices

                # Extract correct answer
                correct_match = re.search(r'Correct Answer:\s*([A-D])', section)
                if correct_match:
                    question_data['correct_answer'] = correct_match.group(1)

                # Extract justifications
                justification_match = re.search(r'Justification:\s*(.+?)(?=\n\s*Target Concept:|$)', section, re.DOTALL)
                if justification_match:
                    justification_text = justification_match.group(1).strip()
                    justifications = {}

                    # Parse individual justifications
                    justification_lines = justification_text.split('\n')
                    for line in justification_lines:
                        line = line.strip()
                        # Match pattern like "- A: Some justification"
                        just_match = re.match(r'^-\s*([A-D]):\s*(.+)$', line)
                        if just_match:
                            choice_letter = just_match.group(1)
                            justification = just_match.group(2).strip()
                            justifications[choice_letter] = justification

                    question_data['justifications'] = justifications

                # Extract other metadata
                metadata_fields = {
                    'target_concept': r'Target Concept:\s*(.+?)(?=\n\s*\w+:|$)',
                    'purpose': r'Purpose:\s*(.+?)(?=\n\s*\w+:|$)',
                    'difficulty': r'Difficulty:\s*(\d+)',
                    'tags': r'Tags:\s*(.+?)(?=\n\s*\w+:|$)'
                }

                for field, pattern in metadata_fields.items():
                    match = re.search(pattern, section, re.DOTALL | re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        # Clean up multi-line values
                        value = re.sub(r'\s+', ' ', value).strip()

                        # Special handling for difficulty (convert to int)
                        if field == 'difficulty':
                            try:
                                question_data[field] = int(value)
                            except ValueError:
                                question_data[field] = 3  # Default difficulty
                        else:
                            question_data[field] = value
                    else:
                        # Provide defaults for missing fields
                        if field == 'difficulty':
                            question_data[field] = 3
                        else:
                            question_data[field] = ""

                # Only add question if it has essential fields
                if (question_data.get('question') and
                    question_data.get('choices') and
                    question_data.get('correct_answer')):
                    questions.append(question_data)

            return questions

        except Exception as e:
            self.logger.error(f"Failed to parse multiple choice questions: {e}")
            # Return empty list on parse failure
            return []

    async def create_post_topic_quiz(
        self,
        topic_title: str,
        core_concept: str,
        user_level: str = "beginner",
        learning_objectives: Optional[List[str]] = None,
        previous_topics: Optional[List[str]] = None,
        key_aspects: Optional[List[str]] = None,
        common_misconceptions: Optional[List[str]] = None,
        preferred_formats: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Create a comprehensive post-topic quiz with mixed question formats.

        Args:
            topic_title: Title of the topic
            core_concept: Core concept to assess
            user_level: User's skill level
            learning_objectives: Learning objectives for the concept
            previous_topics: Previously covered topics
            key_aspects: Key aspects to assess
            common_misconceptions: Common misconceptions to check
            preferred_formats: Preferred question formats

        Returns:
            List of quiz item dictionaries with mixed formats and metadata

        Raises:
            BiteSizedTopicError: If generation fails
        """
        try:
            context = create_default_context(
                user_level=user_level,
                time_constraint=25  # Longer for comprehensive assessment
            )

            messages = self.prompts['post_topic_quiz'].generate_prompt(
                context,
                topic_title=topic_title,
                core_concept=core_concept,
                learning_objectives=learning_objectives or [],
                previous_topics=previous_topics or [],
                key_aspects=key_aspects or [],
                common_misconceptions=common_misconceptions or [],
                preferred_formats=preferred_formats or []
            )

            response = await self.llm_client.generate_response(messages)

            # Parse the structured output
            parsed_quiz = self._parse_post_topic_quiz(response.content)

            # Add generation metadata to each quiz item
            generation_metadata = {
                'generation_prompt': self._format_messages_for_storage(messages),
                'raw_llm_response': response.content
            }
            for item in parsed_quiz:
                item['_generation_metadata'] = generation_metadata

            self.logger.info(f"Generated post-topic quiz with {len(parsed_quiz)} items for '{core_concept}'")
            return parsed_quiz

        except Exception as e:
            self.logger.error(f"Failed to generate post-topic quiz: {e}")
            raise BiteSizedTopicError(f"Failed to generate post-topic quiz: {e}")

    def _parse_post_topic_quiz(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse the structured output from the post-topic quiz prompt.

        Args:
            content: Raw LLM output containing multiple quiz items of different formats

        Returns:
            List of quiz item dictionaries with mixed formats and metadata

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

            quiz_items = []

            # Split by "Item" followed by a number
            item_sections = re.split(r'\n\s*Item\s+\d+\s*\n', content)

            # Remove empty first section if it exists
            if item_sections and not item_sections[0].strip():
                item_sections = item_sections[1:]

            for section in item_sections:
                section = section.strip()
                if not section:
                    continue

                item_data = {}

                # Extract common fields first
                title_match = re.search(r'Title:\s*(.+?)(?=\n|$)', section)
                if title_match:
                    item_data['title'] = title_match.group(1).strip()
                else:
                    # Default title based on type if available
                    type_match = re.search(r'Type:\s*(.+?)(?=\n|$)', section)
                    if type_match:
                        item_data['title'] = type_match.group(1).strip()
                    else:
                        item_data['title'] = "Quiz Item"

                type_match = re.search(r'Type:\s*(.+?)(?=\n|$)', section)
                if type_match:
                    item_data['type'] = type_match.group(1).strip()

                question_match = re.search(r'Question or Prompt:\s*(.+?)(?=\n\s*(?:Choices:|Expected Elements|Dialogue Objective:|Target Concept:))', section, re.DOTALL)
                if question_match:
                    item_data['question'] = question_match.group(1).strip()

                # Extract metadata fields
                metadata_fields = {
                    'target_concept': r'Target Concept:\s*(.+?)(?=\n\s*\w+:|$)',
                    'difficulty': r'Difficulty:\s*(\d+)',
                    'tags': r'Tags:\s*(.+?)(?=\n\s*\w+:|$)'
                }

                for field, pattern in metadata_fields.items():
                    match = re.search(pattern, section, re.DOTALL | re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        value = re.sub(r'\s+', ' ', value).strip()

                        if field == 'difficulty':
                            try:
                                item_data[field] = int(value)
                            except ValueError:
                                item_data[field] = 3
                        else:
                            item_data[field] = value
                    else:
                        if field == 'difficulty':
                            item_data[field] = 3
                        else:
                            item_data[field] = ""

                # Parse format-specific fields based on type
                item_type = item_data.get('type', '').lower()

                if 'multiple choice' in item_type:
                    # Parse Multiple Choice specific fields
                    choices_match = re.search(r'Choices:\s*(.+?)(?=\n\s*Correct Answer:)', section, re.DOTALL)
                    if choices_match:
                        choices_text = choices_match.group(1).strip()
                        choices = {}

                        choice_lines = choices_text.split('\n')
                        for line in choice_lines:
                            line = line.strip()
                            choice_match = re.match(r'^\(?([A-D])\.\s*(.+)$', line)
                            if choice_match:
                                choice_letter = choice_match.group(1)
                                choice_text = choice_match.group(2).strip()
                                choices[choice_letter] = choice_text

                        item_data['choices'] = choices

                    # Extract correct answer
                    correct_match = re.search(r'Correct Answer:\s*([A-D])', section)
                    if correct_match:
                        item_data['correct_answer'] = correct_match.group(1)

                    # Extract justifications
                    justification_match = re.search(r'Justification:\s*(.+?)(?=\n\s*Target Concept:|$)', section, re.DOTALL)
                    if justification_match:
                        justification_text = justification_match.group(1).strip()
                        justifications = {}

                        justification_lines = justification_text.split('\n')
                        for line in justification_lines:
                            line = line.strip()
                            just_match = re.match(r'^-\s*([A-D]):\s*(.+)$', line)
                            if just_match:
                                choice_letter = just_match.group(1)
                                justification = just_match.group(2).strip()
                                justifications[choice_letter] = justification

                        item_data['justifications'] = justifications

                elif 'short answer' in item_type:
                    # Parse Short Answer specific fields
                    expected_match = re.search(r'Expected Elements of a Good Answer:\s*(.+?)(?=\n\s*Target Concept:|$)', section, re.DOTALL)
                    if expected_match:
                        expected_elements = expected_match.group(1).strip()
                        expected_elements = re.sub(r'\s+', ' ', expected_elements).strip()
                        item_data['expected_elements'] = expected_elements

                elif 'assessment dialogue' in item_type or 'dialogue' in item_type:
                    # Parse Assessment Dialogue specific fields
                    dialogue_fields = {
                        'dialogue_objective': r'Dialogue Objective:\s*(.+?)(?=\n\s*\w+:|$)',
                        'scaffolding_prompts': r'Scaffolding Prompts:\s*(.+?)(?=\n\s*\w+:|$)',
                        'exit_criteria': r'Exit Criteria:\s*(.+?)(?=\n\s*\w+:|$)'
                    }

                    for field, pattern in dialogue_fields.items():
                        match = re.search(pattern, section, re.DOTALL | re.IGNORECASE)
                        if match:
                            value = match.group(1).strip()
                            value = re.sub(r'\s+', ' ', value).strip()
                            item_data[field] = value
                        else:
                            item_data[field] = ""

                # Only add item if it has essential fields
                if item_data.get('type') and item_data.get('question'):
                    quiz_items.append(item_data)

            return quiz_items

        except Exception as e:
            self.logger.error(f"Failed to parse post-topic quiz: {e}")
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