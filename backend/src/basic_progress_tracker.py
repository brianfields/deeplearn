"""
Basic Progress Tracker for Learning App

"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from simple_storage import (
    SimpleStorage, SimpleProgress,
    ProgressStatus
)
from data_structures import QuizQuestion, QuizType

@dataclass
class LearningSession:
    """Represents a learning session"""
    path_id: str
    topic_id: str
    session_type: str  # 'lesson' or 'quiz'
    started_at: datetime
    completed_at: Optional[datetime] = None
    time_spent: int = 0  # minutes
    content_data: Dict[str, Any] = {}
    quiz_results: Dict[str, Any] = {}

class BasicProgressTracker:
    """
    Basic progress tracker for learning sessions.

    Handles lesson completion, quiz scoring, and progress advancement
    without the complexity of spaced repetition.
    """

    def __init__(self, storage: SimpleStorage):
        self.storage = storage
        self.mastery_threshold = 0.9  # 90% for mastery
        self.passing_threshold = 0.7  # 70% to advance

    def start_lesson(self, path_id: str, topic_id: str) -> LearningSession:
        """Start a new lesson session"""
        session = LearningSession(
            path_id=path_id,
            topic_id=topic_id,
            session_type='lesson',
            started_at=datetime.now(),
            content_data={}
        )

        # Update progress to in_progress
        progress = self._get_or_create_progress(path_id, topic_id)
        progress.status = ProgressStatus.IN_PROGRESS
        progress.last_studied = datetime.now().isoformat()
        self.storage.update_progress(path_id, topic_id, progress)

        return session

    def complete_lesson(self, session: LearningSession) -> None:
        """Mark lesson as completed"""
        session.completed_at = datetime.now()
        session.time_spent = int((session.completed_at - session.started_at).total_seconds() / 60)

        # Update progress
        progress = self._get_or_create_progress(session.path_id, session.topic_id)
        progress.lesson_completed = True
        progress.time_spent += session.time_spent
        progress.last_studied = datetime.now().isoformat()

        self.storage.update_progress(session.path_id, session.topic_id, progress)

    def start_quiz(self, path_id: str, topic_id: str) -> LearningSession:
        """Start a new quiz session"""
        session = LearningSession(
            path_id=path_id,
            topic_id=topic_id,
            session_type='quiz',
            started_at=datetime.now(),
            quiz_results={}
        )

        return session

    def submit_quiz(
        self,
        session: LearningSession,
        questions: List[QuizQuestion],
        answers: List[str]
    ) -> Dict[str, Any]:
        """Submit quiz answers and calculate score"""
        session.completed_at = datetime.now()
        session.time_spent = int((session.completed_at - session.started_at).total_seconds() / 60)

        # Calculate score
        correct_answers = 0
        total_questions = len(questions)
        question_results = []

        for i, (question, answer) in enumerate(zip(questions, answers)):
            is_correct = self._check_answer(question, answer)
            if is_correct:
                correct_answers += 1

            question_results.append({
                'question': question.question,
                'user_answer': answer,
                'correct_answer': question.correct_answer,
                'is_correct': is_correct,
                'explanation': question.explanation
            })

        score = correct_answers / total_questions if total_questions > 0 else 0

        # Store quiz results
        session.quiz_results = {
            'score': score,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'question_results': question_results
        }

        # Update progress
        progress = self._get_or_create_progress(session.path_id, session.topic_id)
        progress.quiz_completed = True
        progress.attempts += 1
        progress.time_spent += session.time_spent
        progress.last_studied = datetime.now().isoformat()

        # Update score if better
        if score > progress.score:
            progress.score = score

        # Determine new status
        if score >= self.mastery_threshold:
            progress.status = ProgressStatus.MASTERY
        elif score >= self.passing_threshold:
            progress.status = ProgressStatus.PARTIAL
        else:
            progress.status = ProgressStatus.IN_PROGRESS

        self.storage.update_progress(session.path_id, session.topic_id, progress)

        return session.quiz_results

    def _check_answer(self, question: QuizQuestion, user_answer: str) -> bool:
        """Check if user's answer is correct"""
        # Simple string comparison (can be enhanced for fuzzy matching)
        correct = question.correct_answer.strip().lower()
        user = user_answer.strip().lower()

        if question.type == QuizType.MULTIPLE_CHOICE:
            return correct == user
        elif question.type == QuizType.SHORT_ANSWER:
            # Simple contains check for short answers
            return correct in user or user in correct
        else:
            # For scenario critique, just check if answer is substantial
            return len(user) > 10  # Minimum effort check

    def _get_or_create_progress(self, path_id: str, topic_id: str) -> SimpleProgress:
        """Get existing progress or create new one"""
        learning_path = self.storage.load_learning_path(path_id)
        if learning_path and topic_id in learning_path.progress:
            return learning_path.progress[topic_id]
        else:
            return SimpleProgress(
                topic_id=topic_id,
                status=ProgressStatus.NOT_STARTED
            )

    def can_advance_to_next_topic(self, path_id: str, topic_id: str) -> bool:
        """Check if user can advance to next topic"""
        progress = self._get_or_create_progress(path_id, topic_id)

        # Must complete lesson and pass quiz
        return (progress.lesson_completed and
                progress.quiz_completed and
                progress.score >= self.passing_threshold)

    def get_topic_status(self, path_id: str, topic_id: str) -> Dict[str, Any]:
        """Get detailed status for a topic"""
        progress = self._get_or_create_progress(path_id, topic_id)

        return {
            'topic_id': topic_id,
            'status': progress.status,
            'lesson_completed': progress.lesson_completed,
            'quiz_completed': progress.quiz_completed,
            'score': progress.score,
            'attempts': progress.attempts,
            'time_spent': progress.time_spent,
            'last_studied': progress.last_studied,
            'can_advance': self.can_advance_to_next_topic(path_id, topic_id)
        }

    def get_learning_path_status(self, path_id: str) -> Dict[str, Any]:
        """Get overall status for a learning path"""
        learning_path = self.storage.load_learning_path(path_id)
        if not learning_path:
            return {}

        topic_statuses = []
        for topic in learning_path.topics:
            topic_statuses.append(self.get_topic_status(path_id, topic.id))

        # Calculate overall metrics
        total_topics = len(learning_path.topics)
        completed_topics = sum(
            1 for status in topic_statuses
            if status['status'] in ['completed', 'mastered']
        )
        mastered_topics = sum(
            1 for status in topic_statuses
            if status['status'] == 'mastered'
        )

        average_score = sum(status['score'] for status in topic_statuses) / total_topics if total_topics > 0 else 0
        total_time = sum(status['time_spent'] for status in topic_statuses)

        return {
            'path_id': path_id,
            'topic_name': learning_path.topic_name,
            'total_topics': total_topics,
            'completed_topics': completed_topics,
            'mastered_topics': mastered_topics,
            'completion_percentage': (completed_topics / total_topics * 100) if total_topics > 0 else 0,
            'mastery_percentage': (mastered_topics / total_topics * 100) if total_topics > 0 else 0,
            'average_score': average_score,
            'total_time_spent': total_time,
            'current_topic_index': learning_path.current_topic_index,
            'topic_statuses': topic_statuses
        }

    def get_next_recommended_action(self, path_id: str) -> Dict[str, Any]:
        """Get recommended next action for user"""
        learning_path = self.storage.load_learning_path(path_id)
        if not learning_path:
            return {'action': 'error', 'message': 'Learning path not found'}

        current_topic = self.storage.get_current_topic(path_id)
        if not current_topic:
            return {'action': 'complete', 'message': 'All topics completed!'}

        topic_status = self.get_topic_status(path_id, current_topic.id)

        if not topic_status['lesson_completed']:
            return {
                'action': 'lesson',
                'topic_id': current_topic.id,
                'topic_title': current_topic.title,
                'message': f'Start lesson: {current_topic.title}'
            }
        elif not topic_status['quiz_completed']:
            return {
                'action': 'quiz',
                'topic_id': current_topic.id,
                'topic_title': current_topic.title,
                'message': f'Take quiz for: {current_topic.title}'
            }
        elif topic_status['can_advance']:
            # Advance to next topic
            if self.storage.advance_to_next_topic(path_id):
                next_topic = self.storage.get_current_topic(path_id)
                if next_topic:
                    return {
                        'action': 'lesson',
                        'topic_id': next_topic.id,
                        'topic_title': next_topic.title,
                        'message': f'Continue to next topic: {next_topic.title}'
                    }
                else:
                    return {'action': 'complete', 'message': 'All topics completed!'}
            else:
                return {'action': 'complete', 'message': 'All topics completed!'}
        else:
            return {
                'action': 'retry_quiz',
                'topic_id': current_topic.id,
                'topic_title': current_topic.title,
                'message': f'Retake quiz for: {current_topic.title} (Score: {topic_status["score"]:.1%})'
            }

    def reset_topic_progress(self, path_id: str, topic_id: str) -> None:
        """Reset progress for a specific topic"""
        progress = SimpleProgress(
            topic_id=topic_id,
            status=ProgressStatus.NOT_STARTED
        )
        self.storage.update_progress(path_id, topic_id, progress)

    def reset_learning_path(self, path_id: str) -> None:
        """Reset entire learning path progress"""
        learning_path = self.storage.load_learning_path(path_id)
        if learning_path:
            for topic in learning_path.topics:
                self.reset_topic_progress(path_id, topic.id)

            # Reset current topic index
            self.storage.set_current_topic(path_id, 0)

# Example usage
if __name__ == "__main__":
    from simple_storage import SimpleStorage, create_learning_path_from_syllabus

    # Create storage and tracker
    storage = SimpleStorage()
    tracker = BasicProgressTracker(storage)

    # Create a sample learning path
    sample_syllabus = {
        'topic_name': 'Python Basics',
        'description': 'Learn Python programming fundamentals',
        'topics': [
            {
                'title': 'Variables and Data Types',
                'description': 'Learn about variables and basic data types',
                'learning_objectives': ['Understand variables', 'Know basic data types']
            }
        ]
    }

    learning_path = create_learning_path_from_syllabus(sample_syllabus)
    storage.save_learning_path(learning_path)

    # Test progress tracking
    topic_id = learning_path.topics[0].id

    # Start lesson
    session = tracker.start_lesson(learning_path.id, topic_id)
    print(f"Started lesson session: {session.session_type}")

    # Complete lesson
    time.sleep(1)  # Simulate time passage
    tracker.complete_lesson(session)
    print("Lesson completed")

    # Check recommended action
    recommendation = tracker.get_next_recommended_action(learning_path.id)
    print(f"Next action: {recommendation}")