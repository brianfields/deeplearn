# Learning Session Module

## Purpose
This module manages active learning experiences and sessions. It handles the real-time learning flow, session state management, component progression, and immediate session results without managing historical progress or analytics.

## Domain Responsibility
**"Managing active learning sessions and real-time learning experience"**

The Learning Session module owns all aspects of active learning:
- Learning session lifecycle (start, pause, resume, complete)
- Real-time progression through learning components
- Session state management and persistence
- Component interaction tracking and scoring
- Immediate session results and feedback
- Session recovery and continuation

## Architecture

### Module API (Public Interface)
```python
# module_api/learning_session_service.py
class LearningSessionService:
    @staticmethod
    def start_session(topic_id: str, user_id: str) -> LearningSession:
        """Start a new learning session for a topic"""

    @staticmethod
    def get_session(session_id: str) -> LearningSession:
        """Get active session by ID"""

    @staticmethod
    def advance_session(session_id: str, interaction_result: InteractionResult) -> SessionProgress:
        """Process user interaction and advance session"""

    @staticmethod
    def complete_session(session_id: str) -> SessionResults:
        """Complete session and calculate final results"""

    @staticmethod
    def pause_session(session_id: str) -> None:
        """Pause session for later resumption"""

# module_api/types.py
@dataclass
class LearningSession:
    id: str
    topic_id: str
    user_id: str
    start_time: datetime
    current_step: int
    total_steps: int
    status: SessionStatus  # active, paused, completed

@dataclass
class SessionProgress:
    session_id: str
    current_step: int
    total_steps: int
    completion_percentage: float
    current_component: Component

@dataclass
class SessionResults:
    session_id: str
    topic_id: str
    user_id: str
    completion_time: datetime
    total_duration: int  # seconds
    score: float
    interactions: List[InteractionResult]
    mastery_achieved: bool
```

### HTTP API (Frontend Interface)
```python
# http_api/routes.py
@router.post("/api/sessions")
async def start_session(request: StartSessionRequest) -> SessionResponse:
    """Start new learning session"""

@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str) -> SessionDetailResponse:
    """Get current session state"""

@router.post("/api/sessions/{session_id}/interactions")
async def submit_interaction(
    session_id: str,
    interaction: InteractionRequest
) -> SessionProgressResponse:
    """Submit user interaction and get updated progress"""

@router.post("/api/sessions/{session_id}/complete")
async def complete_session(session_id: str) -> SessionResultsResponse:
    """Complete session and get final results"""

@router.post("/api/sessions/{session_id}/pause")
async def pause_session(session_id: str) -> None:
    """Pause session for later resumption"""
```

### Domain Layer (Business Logic)
```python
# domain/entities/session.py
class LearningSession:
    def __init__(self, topic_id: str, user_id: str, components: List[Component]):
        self.topic_id = topic_id
        self.user_id = user_id
        self.components = components
        self.current_step = 0
        self.interactions = []
        self.start_time = datetime.now()

    def advance_step(self, interaction_result: InteractionResult) -> bool:
        """Business logic for advancing to next step"""
        if not self._is_valid_interaction(interaction_result):
            raise InvalidInteractionError()

        self.interactions.append(interaction_result)

        if self._should_advance():
            self.current_step += 1
            return True
        return False

    def calculate_session_score(self) -> float:
        """Business rules for session scoring"""
        correct_interactions = [i for i in self.interactions if i.is_correct]
        return len(correct_interactions) / len(self.interactions) if self.interactions else 0

    def is_completed(self) -> bool:
        """Business logic for session completion"""
        return self.current_step >= len(self.components)

# domain/policies/progression_policy.py
class ProgressionPolicy:
    @staticmethod
    def should_advance_step(interaction_result: InteractionResult, component: Component) -> bool:
        """Business rules for step advancement"""

    @staticmethod
    def calculate_mastery_threshold(component_type: str) -> float:
        """Business rules for mastery thresholds by component type"""

    @staticmethod
    def determine_session_completion(session: LearningSession) -> bool:
        """Business rules for session completion criteria"""
```

### Infrastructure Layer (Technical Implementation)
```python
# infrastructure/repositories/session_repository.py
class SessionRepository:
    @staticmethod
    def save(session: LearningSession) -> LearningSession:
        """Persist session state to database"""

    @staticmethod
    def get_by_id(session_id: str) -> Optional[LearningSession]:
        """Retrieve session from database"""

    @staticmethod
    def get_active_sessions(user_id: str) -> List[LearningSession]:
        """Get user's active sessions"""

# infrastructure/session_adapters/session_cache.py
class SessionCache:
    def cache_session_state(self, session: LearningSession) -> None:
        """Cache session state for quick access"""

    def get_cached_session(self, session_id: str) -> Optional[LearningSession]:
        """Retrieve cached session state"""
```

## Cross-Module Communication

### Provides to Other Modules
- **Learning Analytics Module**: Session results for historical tracking

### Dependencies
- **Content Creation Module**: Topic content and components for learning
- **Infrastructure Module**: Database service, caching service

### Communication Examples
```python
# Get topic content from Content Creation module
from modules.content_creation.module_api import ContentCreationService

topic = ContentCreationService.get_topic(topic_id)
session = LearningSession(topic_id, user_id, topic.components)

# Provide results to Learning Analytics module
session_results = LearningSessionService.complete_session(session_id)
# Analytics module will consume these results for progress tracking
```

## Key Business Rules

1. **Session Progression**: Users must interact with each component before advancing
2. **Scoring Algorithm**: Weighted scoring based on component type and difficulty
3. **Mastery Criteria**: Different mastery thresholds for different component types
4. **Session Timeout**: Sessions auto-pause after 30 minutes of inactivity
5. **Completion Requirements**: All components must be attempted for session completion
6. **Recovery Logic**: Sessions can be resumed from last completed step

## Data Flow

1. **Session Start Workflow**:
   ```
   Start Request → Get Topic Content → Create Session → Initialize State → Return Session
   ```

2. **Learning Progression Workflow**:
   ```
   User Interaction → Validate Input → Update Session State → Calculate Progress → Return Status
   ```

3. **Session Completion Workflow**:
   ```
   Complete Request → Calculate Final Score → Generate Results → Save State → Notify Analytics
   ```

## Testing Strategy

### Domain Tests (Pure Business Logic)
```python
def test_session_advancement():
    session = LearningSession(topic_id, user_id, components)
    interaction = InteractionResult(component_id="1", is_correct=True)

    advanced = session.advance_step(interaction)
    assert advanced == True
    assert session.current_step == 1

def test_session_scoring():
    session = LearningSession(topic_id, user_id, components)
    session.interactions = [
        InteractionResult(is_correct=True),
        InteractionResult(is_correct=False),
        InteractionResult(is_correct=True)
    ]

    score = session.calculate_session_score()
    assert score == 0.67  # 2/3 correct
```

### Service Tests (Orchestration)
```python
@patch('modules.content_creation.module_api.ContentCreationService')
@patch('infrastructure.repositories.SessionRepository')
def test_start_session(mock_content, mock_repo):
    mock_content.get_topic.return_value = mock_topic

    session = LearningSessionService.start_session(topic_id, user_id)

    mock_content.get_topic.assert_called_once_with(topic_id)
    mock_repo.save.assert_called_once()
```

### HTTP Tests (API Endpoints)
```python
def test_start_session_endpoint():
    response = client.post("/api/sessions", json={
        "topic_id": "topic-1",
        "user_id": "user-1"
    })

    assert response.status_code == 201
    assert "session_id" in response.json()

def test_submit_interaction_endpoint():
    response = client.post(f"/api/sessions/{session_id}/interactions", json={
        "component_id": "comp-1",
        "answer": "A",
        "time_spent": 30
    })

    assert response.status_code == 200
    assert "progress" in response.json()
```

## Real-Time Features

### Session State Management
- **Auto-save**: Session state saved after each interaction
- **Recovery**: Sessions can be resumed from any point
- **Timeout Handling**: Automatic pause on inactivity

### Progress Tracking
- **Real-time Updates**: Progress calculated and returned immediately
- **Step Validation**: Each step validated before advancement
- **Completion Detection**: Automatic session completion when all steps done

## Anti-Patterns to Avoid

❌ **Historical progress tracking** (belongs in Analytics module)
❌ **Topic browsing/selection** (belongs in Catalog module)
❌ **Content creation/editing** (belongs in Content Creation module)
❌ **Business logic in HTTP routes**
❌ **Cross-session analytics** (single session focus only)

## Performance Considerations

- **Session Caching**: Cache active session state for quick access
- **Batch Updates**: Batch session state updates to reduce database calls
- **Component Preloading**: Preload next components for smooth progression
- **State Compression**: Compress large session states for storage

## Module Evolution

This module can be extended with:
- **Adaptive Learning**: Adjust difficulty based on performance
- **Collaborative Sessions**: Multi-user learning sessions
- **Session Analytics**: Real-time learning analytics during session
- **Offline Support**: Offline session continuation
- **Session Templates**: Reusable session configurations

The modular architecture ensures these features can be added without affecting content creation or analytics functionality.
