"""
Pydantic models for API requests and responses.

This module contains all the data models used by the FastAPI endpoints
for request validation and response serialization.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class StartTopicRequest(BaseModel):
    """Request model for starting a new learning topic."""
    topic: str = Field(..., description="The topic to learn about")
    user_level: str = Field(default="beginner", description="User's skill level")


class ChatMessage(BaseModel):
    """Request model for chat messages in conversations."""
    message: str = Field(..., description="User's message")
    learning_path_id: str = Field(..., description="Learning path ID")
    topic_id: str = Field(..., description="Topic ID")


class TopicResponse(BaseModel):
    """Response model for individual topic information."""
    id: str
    title: str
    description: str
    learning_objectives: List[str]
    estimated_duration: int
    difficulty_level: int
    bite_sized_topic_id: Optional[str] = None
    has_bite_sized_content: bool = False


class LearningPathResponse(BaseModel):
    """Response model for learning path information."""
    id: str
    topic_name: str
    description: str
    topics: List[TopicResponse]
    current_topic_index: int
    estimated_total_hours: float
    bite_sized_content_info: Optional[Dict[str, Any]] = None


class ConversationResponse(BaseModel):
    """Response model for conversation interactions."""
    session_id: str
    ai_response: str
    progress: Dict[str, Any]
    conversation_state: str


class ProgressResponse(BaseModel):
    """Response model for learning progress information."""
    learning_paths: List[Dict[str, Any]]
    current_session: Optional[Dict[str, Any]]
    overall_stats: Dict[str, Any]


# Bite-Sized Topic Models
class BiteSizedTopicResponse(BaseModel):
    """Response model for bite-sized topic listing."""
    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: List[str]
    key_concepts: List[str]
    estimated_duration: int = 15  # Default 15 minutes
    created_at: str


class ComponentResponse(BaseModel):
    """Response model for individual topic components."""
    component_type: str
    content: Any  # Can be dict, list, or string depending on component type
    metadata: Dict[str, Any] = {}


class BiteSizedTopicDetailResponse(BaseModel):
    """Response model for complete bite-sized topic content."""
    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: List[str]
    key_concepts: List[str]
    key_aspects: List[str]
    target_insights: List[str]
    common_misconceptions: List[str]
    previous_topics: List[str]
    creation_strategy: str
    components: List[ComponentResponse]
    created_at: str
    updated_at: str