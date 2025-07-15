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
        Parse the JSON output from the didactic snippet prompt.

        Args:
            content: Raw LLM output containing JSON

        Returns:
            Dictionary with consolidated content including title and all snippet data

        Raises:
            BiteSizedTopicError: If parsing fails
        """
        try:
            import json

            # Remove code block markers if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]

            # Parse JSON
            parsed_data = json.loads(content.strip())

            # Validate required fields
            if not isinstance(parsed_data, dict):
                raise ValueError("Output is not a JSON object")

            if 'title' not in parsed_data or 'snippet' not in parsed_data:
                raise ValueError("Missing required fields: title and snippet")

            # Return the parsed data with defaults for missing optional fields
            return {
                'title': str(parsed_data['title']).strip(),
                'snippet': str(parsed_data['snippet']).strip(),
                'type': parsed_data.get('type', 'didactic_snippet'),
                'difficulty': int(parsed_data.get('difficulty', 2))
            }

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse didactic snippet JSON: {e}")
            # Fallback to try to extract from non-JSON format for backward compatibility
            return self._parse_didactic_snippet_fallback(content)
        except Exception as e:
            self.logger.error(f"Failed to parse didactic snippet: {e}")
            # Return a fallback structure
            return {
                'title': "Didactic Snippet",
                'snippet': content.strip(),
                'type': 'didactic_snippet',
                'difficulty': 2
            }

    def _parse_didactic_snippet_fallback(self, content: str) -> Dict[str, Any]:
        """Fallback parser for non-JSON didactic snippet format."""
        try:
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
                'snippet': snippet,
                'type': 'didactic_snippet',
                'difficulty': 2
            }
        except Exception:
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
        Parse the JSON output from the glossary prompt.

        Args:
            content: Raw LLM output containing JSON with glossary entries

        Returns:
            List of glossary entry dictionaries with consolidated content

        Raises:
            BiteSizedTopicError: If parsing fails
        """
        try:
            import json

            # Remove code block markers if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]

            # Parse JSON
            parsed_data = json.loads(content.strip())

            # Validate structure
            if not isinstance(parsed_data, dict) or 'glossary_entries' not in parsed_data:
                raise ValueError("Invalid JSON structure: missing glossary_entries array")

            glossary_entries = []
            for i, entry_data in enumerate(parsed_data['glossary_entries'], 1):
                if not isinstance(entry_data, dict):
                    continue

                # Validate required fields
                if 'concept' not in entry_data or 'explanation' not in entry_data:
                    self.logger.warning(f"Skipping glossary entry {i}: missing required fields")
                    continue

                # Build the entry with defaults for missing optional fields
                glossary_entry = {
                    'type': entry_data.get('type', 'glossary_entry'),
                    'number': i,
                    'concept': str(entry_data['concept']).strip(),
                    'title': str(entry_data.get('title', f"Glossary: {entry_data['concept']}")),
                    'explanation': str(entry_data['explanation']).strip(),
                    'difficulty': int(entry_data.get('difficulty', 2))
                }

                glossary_entries.append(glossary_entry)

            return glossary_entries

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse glossary JSON: {e}")
            # Fallback to old parsing method for backward compatibility
            return self._parse_glossary_fallback(content)
        except Exception as e:
            self.logger.error(f"Failed to parse glossary: {e}")
            return []

    def _parse_glossary_fallback(self, content: str) -> List[Dict[str, Any]]:
        """Fallback parser for non-JSON glossary format."""
        try:
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
                    explanation = re.sub(r'\s+', ' ', explanation).strip()
                    glossary_entry['explanation'] = explanation

                glossary_entry['difficulty'] = 2

                # Only add if we have essential fields
                if glossary_entry.get('concept') and glossary_entry.get('explanation'):
                    glossary_entries.append(glossary_entry)

            return glossary_entries
        except Exception:
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
        Parse the JSON output from the Socratic dialogue prompt.

        Args:
            content: Raw LLM output containing JSON with dialogues array

        Returns:
            List of dialogue dictionaries with consolidated content and metadata

        Raises:
            BiteSizedTopicError: If parsing fails
        """
        try:
            import json

            # Remove code block markers if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]

            # Parse JSON
            parsed_data = json.loads(content.strip())

            # Validate structure
            if not isinstance(parsed_data, dict) or 'dialogues' not in parsed_data:
                raise ValueError("Invalid JSON structure: missing dialogues array")

            dialogues = []
            for i, dialogue_data in enumerate(parsed_data['dialogues'], 1):
                if not isinstance(dialogue_data, dict):
                    continue

                # Validate required fields
                required_fields = ['concept', 'starting_prompt']
                if not all(field in dialogue_data for field in required_fields):
                    self.logger.warning(f"Skipping Socratic dialogue {i}: missing required fields")
                    continue

                # Build the dialogue with defaults for missing optional fields
                parsed_dialogue = {
                    'type': dialogue_data.get('type', 'socratic_dialogue'),
                    'number': i,
                    'title': str(dialogue_data.get('title', f"Socratic Dialogue {i}")),
                    'concept': str(dialogue_data['concept']).strip(),
                    'dialogue_objective': str(dialogue_data.get('dialogue_objective', '')),
                    'starting_prompt': str(dialogue_data['starting_prompt']).strip(),
                    'dialogue_style': str(dialogue_data.get('dialogue_style', '')),
                    'hints_and_scaffolding': str(dialogue_data.get('hints_and_scaffolding', '')),
                    'exit_criteria': str(dialogue_data.get('exit_criteria', '')),
                    'difficulty': int(dialogue_data.get('difficulty', 3)),
                    'tags': str(dialogue_data.get('tags', ''))
                }

                dialogues.append(parsed_dialogue)

            return dialogues

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Socratic dialogues JSON: {e}")
            # Fallback to old parsing method for backward compatibility
            return self._parse_socratic_dialogues_fallback(content)
        except Exception as e:
            self.logger.error(f"Failed to parse Socratic dialogues: {e}")
            return []

    def _parse_socratic_dialogues_fallback(self, content: str) -> List[Dict[str, Any]]:
        """Fallback parser for non-JSON Socratic dialogues format."""
        try:
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

                # Extract basic fields with simple regex
                concept_match = re.search(r'Concept:\s*([^\n]+)', section)
                if concept_match:
                    dialogue['concept'] = concept_match.group(1).strip()

                starting_prompt_match = re.search(r'Starting\s+Prompt:\s*([^\n]+)', section, re.IGNORECASE)
                if starting_prompt_match:
                    dialogue['starting_prompt'] = starting_prompt_match.group(1).strip()

                # Set defaults for other fields
                dialogue['title'] = f"Socratic Dialogue {i}"
                dialogue['dialogue_objective'] = ""
                dialogue['dialogue_style'] = ""
                dialogue['hints_and_scaffolding'] = ""
                dialogue['exit_criteria'] = ""
                dialogue['difficulty'] = 3
                dialogue['tags'] = ""

                # Only add dialogue if it has essential fields
                if dialogue.get('concept') and dialogue.get('starting_prompt'):
                    dialogues.append(dialogue)

            return dialogues
        except Exception:
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
        Parse the JSON output from the short answer questions prompt.

        Args:
            content: Raw LLM output containing JSON with questions array

        Returns:
            List of question dictionaries with consolidated content and metadata

        Raises:
            BiteSizedTopicError: If parsing fails
        """
        try:
            import json

            # Remove code block markers if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]

            # Parse JSON
            parsed_data = json.loads(content.strip())

            # Validate structure
            if not isinstance(parsed_data, dict) or 'questions' not in parsed_data:
                raise ValueError("Invalid JSON structure: missing questions array")

            questions = []
            for i, question_data in enumerate(parsed_data['questions'], 1):
                if not isinstance(question_data, dict):
                    continue

                # Validate required fields
                required_fields = ['question', 'purpose']
                if not all(field in question_data for field in required_fields):
                    self.logger.warning(f"Skipping short answer question {i}: missing required fields")
                    continue

                # Build the question with defaults for missing optional fields
                parsed_question = {
                    'type': question_data.get('type', 'short_answer_question'),
                    'number': i,
                    'title': str(question_data.get('title', f"Short Answer Question {i}")),
                    'question': str(question_data['question']).strip(),
                    'purpose': str(question_data['purpose']).strip(),
                    'target_concept': str(question_data.get('target_concept', '')),
                    'expected_elements': str(question_data.get('expected_elements', '')),
                    'difficulty': int(question_data.get('difficulty', 3)),
                    'tags': str(question_data.get('tags', ''))
                }

                questions.append(parsed_question)

            return questions

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse short answer questions JSON: {e}")
            # Fallback to old parsing method for backward compatibility
            return self._parse_short_answer_questions_fallback(content)
        except Exception as e:
            self.logger.error(f"Failed to parse short answer questions: {e}")
            return []

    def _parse_short_answer_questions_fallback(self, content: str) -> List[Dict[str, Any]]:
        """Fallback parser for non-JSON short answer questions format."""
        try:
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

                # Extract basic fields with simple regex
                question_match = re.search(r'Question:\s*(.+?)(?=\n\s*\w+:|$)', section, re.DOTALL)
                if question_match:
                    question_data['question'] = question_match.group(1).strip()

                purpose_match = re.search(r'Purpose:\s*(.+?)(?=\n\s*\w+:|$)', section, re.DOTALL)
                if purpose_match:
                    question_data['purpose'] = purpose_match.group(1).strip()

                # Set defaults
                question_data['title'] = f"Short Answer Question {i}"
                question_data['target_concept'] = ""
                question_data['expected_elements'] = ""
                question_data['difficulty'] = 3
                question_data['tags'] = ""

                # Only add question if it has essential fields
                if question_data.get('question') and question_data.get('purpose'):
                    questions.append(question_data)

            return questions
        except Exception:
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
        Parse the JSON output from the multiple choice questions prompt.

        Args:
            content: Raw LLM output containing JSON with questions array

        Returns:
            List of MCQ dictionaries with metadata and justifications

        Raises:
            BiteSizedTopicError: If parsing fails
        """
        try:
            import json

            # Remove code block markers if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]

            # Parse JSON
            parsed_data = json.loads(content.strip())

            # Validate structure
            if not isinstance(parsed_data, dict) or 'questions' not in parsed_data:
                raise ValueError("Invalid JSON structure: missing questions array")

            questions = []
            for i, question_data in enumerate(parsed_data['questions'], 1):
                if not isinstance(question_data, dict):
                    continue

                # Validate required fields
                required_fields = ['question', 'choices', 'correct_answer']
                if not all(field in question_data for field in required_fields):
                    self.logger.warning(f"Skipping MCQ {i}: missing required fields")
                    continue

                # Build the question with defaults for missing optional fields
                parsed_question = {
                    'type': question_data.get('type', 'multiple_choice_question'),
                    'number': i,
                    'title': str(question_data.get('title', f"Multiple Choice Question {i}")),
                    'question': str(question_data['question']).strip(),
                    'choices': question_data['choices'],
                    'correct_answer': str(question_data['correct_answer']).strip(),
                    'justifications': question_data.get('justifications', {}),
                    'target_concept': str(question_data.get('target_concept', '')),
                    'purpose': str(question_data.get('purpose', '')),
                    'difficulty': int(question_data.get('difficulty', 3)),
                    'tags': str(question_data.get('tags', ''))
                }

                # Validate choices structure
                if not isinstance(parsed_question['choices'], dict):
                    self.logger.warning(f"Skipping MCQ {i}: choices must be a dictionary")
                    continue

                # Validate correct answer is in choices
                if parsed_question['correct_answer'] not in parsed_question['choices']:
                    self.logger.warning(f"Skipping MCQ {i}: correct answer not found in choices")
                    continue

                questions.append(parsed_question)

            return questions

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse multiple choice questions JSON: {e}")
            # Fallback to old parsing method for backward compatibility
            return self._parse_multiple_choice_questions_fallback(content)
        except Exception as e:
            self.logger.error(f"Failed to parse multiple choice questions: {e}")
            return []

    def _parse_multiple_choice_questions_fallback(self, content: str) -> List[Dict[str, Any]]:
        """Fallback parser for non-JSON multiple choice questions format."""
        try:
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

                # Extract title, question, choices, etc. (simplified version of original logic)
                title_match = re.search(r'Title:\s*(.+?)(?=\n\s*Question:)', section, re.DOTALL)
                if title_match:
                    question_data['title'] = title_match.group(1).strip()
                else:
                    question_data['title'] = f"Multiple Choice Question {i}"

                question_match = re.search(r'Question:\s*(.+?)(?=\n\s*Choices:)', section, re.DOTALL)
                if question_match:
                    question_data['question'] = question_match.group(1).strip()

                # Extract choices and other fields with basic regex
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
                    question_data['choices'] = choices

                correct_match = re.search(r'Correct Answer:\s*([A-D])', section)
                if correct_match:
                    question_data['correct_answer'] = correct_match.group(1)

                # Set defaults for other fields
                question_data['justifications'] = {}
                question_data['target_concept'] = ""
                question_data['purpose'] = ""
                question_data['difficulty'] = 3
                question_data['tags'] = ""

                # Only add question if it has essential fields
                if (question_data.get('question') and
                    question_data.get('choices') and
                    question_data.get('correct_answer')):
                    questions.append(question_data)

            return questions
        except Exception:
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
        Parse the JSON output from the post-topic quiz prompt.

        Args:
            content: Raw LLM output containing JSON with quiz_items array

        Returns:
            List of quiz item dictionaries with mixed formats and metadata

        Raises:
            BiteSizedTopicError: If parsing fails
        """
        try:
            import json

            # Remove code block markers if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]

            # Parse JSON
            parsed_data = json.loads(content.strip())

            # Validate structure
            if not isinstance(parsed_data, dict) or 'quiz_items' not in parsed_data:
                raise ValueError("Invalid JSON structure: missing quiz_items array")

            quiz_items = []
            for i, item_data in enumerate(parsed_data['quiz_items'], 1):
                if not isinstance(item_data, dict):
                    continue

                # Validate required fields
                required_fields = ['type', 'question']
                if not all(field in item_data for field in required_fields):
                    self.logger.warning(f"Skipping quiz item {i}: missing required fields")
                    continue

                # Build the base item with defaults for missing optional fields
                parsed_item = {
                    'title': str(item_data.get('title', f"Quiz Item {i}")),
                    'type': str(item_data['type']).strip(),
                    'question': str(item_data['question']).strip(),
                    'target_concept': str(item_data.get('target_concept', '')),
                    'difficulty': int(item_data.get('difficulty', 3)),
                    'tags': str(item_data.get('tags', ''))
                }

                # Add type-specific fields based on item type
                item_type = parsed_item['type'].lower()

                if 'multiple choice' in item_type:
                    # Add Multiple Choice specific fields
                    parsed_item['choices'] = item_data.get('choices', {})
                    parsed_item['correct_answer'] = str(item_data.get('correct_answer', '')).strip()
                    parsed_item['justifications'] = item_data.get('justifications', {})

                elif 'short answer' in item_type:
                    # Add Short Answer specific fields
                    parsed_item['expected_elements'] = str(item_data.get('expected_elements', ''))

                elif 'assessment dialogue' in item_type or 'dialogue' in item_type:
                    # Add Assessment Dialogue specific fields
                    parsed_item['dialogue_objective'] = str(item_data.get('dialogue_objective', ''))
                    parsed_item['scaffolding_prompts'] = str(item_data.get('scaffolding_prompts', ''))
                    parsed_item['exit_criteria'] = str(item_data.get('exit_criteria', ''))

                quiz_items.append(parsed_item)

            return quiz_items

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse post-topic quiz JSON: {e}")
            # Fallback to old parsing method for backward compatibility
            return self._parse_post_topic_quiz_fallback(content)
        except Exception as e:
            self.logger.error(f"Failed to parse post-topic quiz: {e}")
            return []

    def _parse_post_topic_quiz_fallback(self, content: str) -> List[Dict[str, Any]]:
        """Fallback parser for non-JSON post-topic quiz format."""
        try:
            quiz_items = []
            # Split by "Item" followed by a number
            item_sections = re.split(r'\n\s*Item\s+\d+\s*\n', content)

            # Remove empty first section if it exists
            if item_sections and not item_sections[0].strip():
                item_sections = item_sections[1:]

            for i, section in enumerate(item_sections, 1):
                section = section.strip()
                if not section:
                    continue

                item_data = {}

                # Extract basic fields
                type_match = re.search(r'Type:\s*(.+?)(?=\n|$)', section)
                if type_match:
                    item_data['type'] = type_match.group(1).strip()

                question_match = re.search(r'Question or Prompt:\s*(.+?)(?=\n\s*(?:Choices:|Expected Elements|Dialogue Objective:|Target Concept:))', section, re.DOTALL)
                if question_match:
                    item_data['question'] = question_match.group(1).strip()

                # Set defaults
                item_data['title'] = f"Quiz Item {i}"
                item_data['target_concept'] = ""
                item_data['difficulty'] = 3
                item_data['tags'] = ""

                # Only add item if it has essential fields
                if item_data.get('type') and item_data.get('question'):
                    quiz_items.append(item_data)

            return quiz_items
        except Exception:
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