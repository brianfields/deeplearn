"""
Simple File-Based Storage for Learning App

This module provides basic data persistence using JSON files.
Perfect for prototyping and getting started quickly.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from data_structures import ProgressStatus

@dataclass
class SimpleTopic:
    """Simplified topic structure"""
    id: str
    title: str
    description: str
    learning_objectives: List[str]
    position: int
    bite_sized_topic_id: Optional[str] = None  # Reference to bite-sized content
    has_bite_sized_content: bool = False

@dataclass
class SimpleProgress:
    """Simplified progress tracking"""
    topic_id: str
    status: ProgressStatus
    score: float = 0.0
    attempts: int = 0
    time_spent: int = 0  # minutes
    last_studied: Optional[str] = None
    lesson_completed: bool = False
    quiz_completed: bool = False

@dataclass
class SimpleLearningPath:
    """Simplified learning path"""
    id: str
    topic_name: str
    description: str
    topics: List[SimpleTopic]
    progress: Dict[str, SimpleProgress]
    created_at: str
    last_accessed: str
    current_topic_index: int = 0

class SimpleStorage:
    """
    Simple file-based storage for learning data.

    Stores all data in JSON files in a .learning_data directory.
    """

    def __init__(self, data_dir: str = ".learning_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # File paths
        self.learning_paths_file = self.data_dir / "learning_paths.json"
        self.current_session_file = self.data_dir / "current_session.json"
        self.settings_file = self.data_dir / "settings.json"

    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON data from file"""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading {file_path}: {e}")
                return {}
        return {}

    def _save_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Save data to JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving {file_path}: {e}")

    def save_learning_path(self, learning_path: SimpleLearningPath) -> None:
        """Save a learning path"""
        data = self._load_json(self.learning_paths_file)
        data[learning_path.id] = asdict(learning_path)
        self._save_json(self.learning_paths_file, data)

    def load_learning_path(self, path_id: str) -> Optional[SimpleLearningPath]:
        """Load a learning path by ID"""
        data = self._load_json(self.learning_paths_file)
        if path_id in data:
            path_data = data[path_id]

            # Convert topics back to SimpleTopic objects
            topics = [SimpleTopic(**topic) for topic in path_data['topics']]

            # Convert progress back to SimpleProgress objects
            progress = {
                topic_id: SimpleProgress(**prog_data)
                for topic_id, prog_data in path_data['progress'].items()
            }

            return SimpleLearningPath(
                id=path_data['id'],
                topic_name=path_data['topic_name'],
                description=path_data['description'],
                topics=topics,
                progress=progress,
                created_at=path_data['created_at'],
                last_accessed=path_data['last_accessed'],
                current_topic_index=path_data.get('current_topic_index', 0)
            )
        return None

    def list_learning_paths(self) -> List[Dict[str, Any]]:
        """List all learning paths"""
        data = self._load_json(self.learning_paths_file)
        return [
            {
                'id': path_id,
                'topic_name': path_data['topic_name'],
                'description': path_data['description'],
                'created_at': path_data['created_at'],
                'last_accessed': path_data['last_accessed'],
                'topics_count': len(path_data['topics']),
                'progress_count': len([p for p in path_data['progress'].values() if p['status'] != 'not_started'])
            }
            for path_id, path_data in data.items()
        ]

    def get_all_learning_paths(self) -> List[SimpleLearningPath]:
        """Get all learning paths as SimpleLearningPath objects"""
        data = self._load_json(self.learning_paths_file)
        paths = []

        for path_id in data.keys():
            path = self.load_learning_path(path_id)
            if path:
                paths.append(path)

        return sorted(paths, key=lambda x: x.last_accessed, reverse=True)

    def get_learning_path(self, path_id: str) -> Optional[SimpleLearningPath]:
        """Alias for load_learning_path for consistency"""
        return self.load_learning_path(path_id)

    def delete_learning_path(self, path_id: str) -> bool:
        """Delete a learning path"""
        data = self._load_json(self.learning_paths_file)
        if path_id in data:
            del data[path_id]
            self._save_json(self.learning_paths_file, data)
            return True
        return False

    def update_progress(self, path_id: str, topic_id: str, progress: SimpleProgress) -> None:
        """Update progress for a specific topic"""
        learning_path = self.load_learning_path(path_id)
        if learning_path:
            learning_path.progress[topic_id] = progress
            learning_path.last_accessed = datetime.now().isoformat()
            self.save_learning_path(learning_path)

    def get_current_topic(self, path_id: str) -> Optional[SimpleTopic]:
        """Get the current topic for a learning path"""
        learning_path = self.load_learning_path(path_id)
        if learning_path and learning_path.current_topic_index < len(learning_path.topics):
            return learning_path.topics[learning_path.current_topic_index]
        return None

    def advance_to_next_topic(self, path_id: str) -> bool:
        """Advance to the next topic in the learning path"""
        learning_path = self.load_learning_path(path_id)
        if learning_path:
            if learning_path.current_topic_index < len(learning_path.topics) - 1:
                learning_path.current_topic_index += 1
                learning_path.last_accessed = datetime.now().isoformat()
                self.save_learning_path(learning_path)
                return True
        return False

    def set_current_topic(self, path_id: str, topic_index: int) -> bool:
        """Set the current topic index"""
        learning_path = self.load_learning_path(path_id)
        if learning_path and 0 <= topic_index < len(learning_path.topics):
            learning_path.current_topic_index = topic_index
            learning_path.last_accessed = datetime.now().isoformat()
            self.save_learning_path(learning_path)
            return True
        return False

    def update_topic_bite_sized_content(self, path_id: str, topic_index: int, bite_sized_topic_id: str) -> bool:
        """Update a topic to include bite-sized content reference"""
        learning_path = self.load_learning_path(path_id)
        if learning_path and 0 <= topic_index < len(learning_path.topics):
            learning_path.topics[topic_index].bite_sized_topic_id = bite_sized_topic_id
            learning_path.topics[topic_index].has_bite_sized_content = True
            learning_path.last_accessed = datetime.now().isoformat()
            self.save_learning_path(learning_path)
            return True
        return False

    def save_current_session(self, session_data: Dict[str, Any]) -> None:
        """Save current session data"""
        self._save_json(self.current_session_file, session_data)

    def load_current_session(self) -> Dict[str, Any]:
        """Load current session data"""
        return self._load_json(self.current_session_file)

    def clear_current_session(self) -> None:
        """Clear current session data"""
        if self.current_session_file.exists():
            self.current_session_file.unlink()

    def save_settings(self, settings: Dict[str, Any]) -> None:
        """Save user settings"""
        self._save_json(self.settings_file, settings)

    def load_settings(self) -> Dict[str, Any]:
        """Load user settings"""
        default_settings = {
            'user_level': 'beginner',
            'lesson_duration': 15,
            'openai_api_key': '',
            'openai_model': 'gpt-3.5-turbo'
        }
        settings = self._load_json(self.settings_file)
        return {**default_settings, **settings}

    def get_progress_summary(self, path_id: str) -> Dict[str, Any]:
        """Get progress summary for a learning path"""
        learning_path = self.load_learning_path(path_id)
        if not learning_path:
            return {}

        total_topics = len(learning_path.topics)
        completed_topics = sum(
            1 for p in learning_path.progress.values()
            if p.status in [ProgressStatus.PARTIAL, ProgressStatus.MASTERY]
        )

        return {
            'total_topics': total_topics,
            'completed_topics': completed_topics,
            'completion_percentage': (completed_topics / total_topics * 100) if total_topics > 0 else 0,
            'current_topic_index': learning_path.current_topic_index,
            'current_topic_title': learning_path.topics[learning_path.current_topic_index].title if learning_path.current_topic_index < len(learning_path.topics) else None,
            'total_time_spent': sum(p.time_spent for p in learning_path.progress.values())
        }

# Helper functions
def create_learning_path_from_syllabus(syllabus: Dict[str, Any]) -> SimpleLearningPath:
    """Create a SimpleLearningPath from a syllabus"""
    path_id = generate_unique_id("path")

    topics = []
    progress = {}

    # Get bite-sized content info if available
    bite_sized_info = syllabus.get('bite_sized_content', {})
    generated_topics = {item['topic_index']: item for item in bite_sized_info.get('generated_topics', [])}

    for i, topic_data in enumerate(syllabus['topics']):
        topic_id = generate_unique_id("topic")

        # Check if this topic has bite-sized content
        bite_sized_data = generated_topics.get(i)
        bite_sized_topic_id = bite_sized_data.get('topic_id') if bite_sized_data else None
        has_bite_sized_content = bite_sized_data.get('has_bite_sized_content', False) if bite_sized_data else False

        topic = SimpleTopic(
            id=topic_id,
            title=topic_data['title'],
            description=topic_data['description'],
            learning_objectives=topic_data['learning_objectives'],
            position=i,
            bite_sized_topic_id=bite_sized_topic_id,
            has_bite_sized_content=has_bite_sized_content
        )
        topics.append(topic)

        # Initialize progress
        progress[topic_id] = SimpleProgress(
            topic_id=topic_id,
            status=ProgressStatus.NOT_STARTED
        )

    return SimpleLearningPath(
        id=path_id,
        topic_name=syllabus['topic_name'],
        description=syllabus['description'],
        topics=topics,
        progress=progress,
        created_at=datetime.now().isoformat(),
        last_accessed=datetime.now().isoformat(),
        current_topic_index=0
    )

def generate_unique_id(prefix: str = "item") -> str:
    """Generate a unique ID"""
    import uuid
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    short_uuid = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{short_uuid}"

# Example usage
if __name__ == "__main__":
    # Example usage
    storage = SimpleStorage()

    # Create a sample learning path
    sample_syllabus = {
        'topic_name': 'Python Basics',
        'description': 'Learn Python programming fundamentals',
        'topics': [
            {
                'title': 'Variables and Data Types',
                'description': 'Learn about variables and basic data types',
                'learning_objectives': ['Understand variables', 'Know basic data types']
            },
            {
                'title': 'Control Flow',
                'description': 'Learn about if statements and loops',
                'learning_objectives': ['Use if statements', 'Write loops']
            }
        ]
    }

    # Create and save learning path
    learning_path = create_learning_path_from_syllabus(sample_syllabus)
    storage.save_learning_path(learning_path)

    # List learning paths
    paths = storage.list_learning_paths()
    print(f"Learning paths: {paths}")

    # Get progress summary
    summary = storage.get_progress_summary(learning_path.id)
    print(f"Progress summary: {summary}")