# Learning Analytics Module

## Purpose
This module manages historical learning data, progress tracking across sessions, and learning insights. It provides analytics, achievements, and long-term progress visualization without managing active learning sessions.

## Domain Responsibility
**"Tracking learning progress and providing insights over time"**

The Learning Analytics module owns all aspects of learning analytics:
- Cross-session progress tracking and aggregation
- Learning streaks and achievement calculation
- Performance analytics and insights
- Goal setting and progress toward goals
- Historical learning data management
- Learning pattern analysis and recommendations

## Architecture

### Module API (Public Interface)
```python
# module_api/learning_analytics_service.py
class LearningAnalyticsService:
    @staticmethod
    def record_session_completion(session_results: SessionResults) -> None:
        """Record completed session for progress tracking"""

    @staticmethod
    def get_topic_progress(user_id: str, topic_id: str) -> TopicProgress:
        """Get user's progress on a specific topic"""

    @staticmethod
    def get_overall_progress(user_id: str) -> OverallProgress:
        """Get user's overall learning progress and statistics"""

    @staticmethod
    def get_learning_streaks(user_id: str) -> LearningStreaks:
        """Get user's learning streaks and consistency metrics"""

    @staticmethod
    def get_achievements(user_id: str) -> List[Achievement]:
        """Get user's earned achievements and badges"""

    @staticmethod
    def get_learning_insights(user_id: str) -> LearningInsights:
        """Get personalized learning insights and recommendations"""

# module_api/types.py
@dataclass
class TopicProgress:
    topic_id: str
    user_id: str
    completion_percentage: float
    best_score: float
    total_time_spent: int  # seconds
    sessions_completed: int
    last_session_date: datetime
    mastery_level: MasteryLevel

@dataclass
class OverallProgress:
    user_id: str
    topics_started: int
    topics_completed: int
    total_time_spent: int
    average_score: float
    learning_velocity: float  # topics per week

@dataclass
class LearningStreaks:
    current_streak: int  # consecutive days
    longest_streak: int
    weekly_consistency: float  # percentage
    monthly_activity: Dict[str, int]  # month -> session count
```

### HTTP API (Frontend Interface)
```python
# http_api/routes.py
@router.get("/api/analytics/users/{user_id}/progress")
async def get_overall_progress(user_id: str) -> OverallProgressResponse:
    """Get user's overall learning progress"""

@router.get("/api/analytics/users/{user_id}/topics/{topic_id}/progress")
async def get_topic_progress(user_id: str, topic_id: str) -> TopicProgressResponse:
    """Get progress on specific topic"""

@router.get("/api/analytics/users/{user_id}/streaks")
async def get_learning_streaks(user_id: str) -> StreaksResponse:
    """Get learning streaks and consistency data"""

@router.get("/api/analytics/users/{user_id}/achievements")
async def get_achievements(user_id: str) -> AchievementsResponse:
    """Get earned achievements and badges"""

@router.get("/api/analytics/users/{user_id}/insights")
async def get_learning_insights(user_id: str) -> InsightsResponse:
    """Get personalized learning insights"""

@router.post("/api/analytics/sessions")
async def record_session(session_data: SessionResultsRequest) -> None:
    """Record completed session (called by Learning Session module)"""
```

### Domain Layer (Business Logic)
```python
# domain/entities/progress.py
class LearningProgress:
    def __init__(self, user_id: str, topic_id: str):
        self.user_id = user_id
        self.topic_id = topic_id
        self.sessions = []
        self.total_time_spent = 0
        self.best_score = 0.0

    def update_from_session(self, session_results: SessionResults) -> None:
        """Business logic for updating progress from session"""
        self.sessions.append(session_results)
        self.total_time_spent += session_results.duration
        self.best_score = max(self.best_score, session_results.score)

    def calculate_mastery_level(self) -> MasteryLevel:
        """Business rules for determining mastery level"""
        if self.best_score >= 0.9 and len(self.sessions) >= 2:
            return MasteryLevel.MASTERED
        elif self.best_score >= 0.7:
            return MasteryLevel.PROFICIENT
        elif len(self.sessions) > 0:
            return MasteryLevel.LEARNING
        else:
            return MasteryLevel.NOT_STARTED

    def calculate_completion_percentage(self) -> float:
        """Business logic for completion percentage"""
        if not self.sessions:
            return 0.0
        latest_session = max(self.sessions, key=lambda s: s.completion_time)
        return latest_session.completion_percentage

# domain/policies/achievement_policy.py
class AchievementPolicy:
    @staticmethod
    def check_streak_achievements(streak_days: int) -> List[Achievement]:
        """Business rules for streak-based achievements"""
        achievements = []
        if streak_days >= 7:
            achievements.append(Achievement("WEEK_STREAK", "7-day learning streak"))
        if streak_days >= 30:
            achievements.append(Achievement("MONTH_STREAK", "30-day learning streak"))
        return achievements

    @staticmethod
    def check_mastery_achievements(mastered_topics: int) -> List[Achievement]:
        """Business rules for mastery-based achievements"""
        achievements = []
        if mastered_topics >= 5:
            achievements.append(Achievement("MASTER_LEARNER", "Mastered 5 topics"))
        return achievements
```

### Infrastructure Layer (Technical Implementation)
```python
# infrastructure/repositories/progress_repository.py
class ProgressRepository:
    @staticmethod
    def save_progress(progress: LearningProgress) -> None:
        """Persist progress data to database"""

    @staticmethod
    def get_user_progress(user_id: str) -> List[LearningProgress]:
        """Get all progress data for user"""

    @staticmethod
    def get_topic_progress(user_id: str, topic_id: str) -> Optional[LearningProgress]:
        """Get progress for specific topic"""

# infrastructure/analytics_adapters/metrics_calculator.py
class MetricsCalculator:
    def calculate_learning_velocity(self, sessions: List[SessionResults]) -> float:
        """Calculate topics completed per week"""

    def calculate_consistency_score(self, session_dates: List[datetime]) -> float:
        """Calculate learning consistency percentage"""

    def generate_insights(self, progress_data: List[LearningProgress]) -> LearningInsights:
        """Generate personalized learning insights"""
```

## Cross-Module Communication

### Provides to Other Modules
- **Topic Catalog Module**: Progress data for topic display
- **Learning Session Module**: Historical context for adaptive learning

### Dependencies
- **Learning Session Module**: Session results for progress calculation
- **Infrastructure Module**: Database service, analytics tools

### Communication Examples
```python
# Receive session results from Learning Session module
from modules.learning_session.module_api import SessionResults

def record_session_completion(session_results: SessionResults) -> None:
    progress = get_or_create_progress(session_results.user_id, session_results.topic_id)
    progress.update_from_session(session_results)
    ProgressRepository.save_progress(progress)

# Provide progress data to Topic Catalog module
progress = LearningAnalyticsService.get_topic_progress(user_id, topic_id)
# Topic Catalog uses this for progress indicators
```

## Key Business Rules

1. **Progress Calculation**: Progress based on best session performance, not average
2. **Mastery Levels**: Clear criteria for Not Started → Learning → Proficient → Mastered
3. **Streak Calculation**: Consecutive days with at least one completed session
4. **Achievement Unlocking**: Achievements unlocked immediately when criteria met
5. **Consistency Scoring**: Based on regularity of learning sessions over time
6. **Insight Generation**: Personalized recommendations based on learning patterns

## Data Flow

1. **Progress Recording Workflow**:
   ```
   Session Completion → Extract Results → Update Progress → Calculate Achievements → Store Data
   ```

2. **Progress Retrieval Workflow**:
   ```
   Progress Request → Retrieve Data → Calculate Metrics → Generate Insights → Return Analytics
   ```

3. **Achievement Workflow**:
   ```
   Progress Update → Check Achievement Criteria → Unlock New Achievements → Notify User
   ```

## Testing Strategy

### Domain Tests (Pure Business Logic)
```python
def test_mastery_level_calculation():
    progress = LearningProgress(user_id, topic_id)
    session_result = SessionResults(score=0.95, completion_percentage=100)

    progress.update_from_session(session_result)
    progress.update_from_session(session_result)  # Second session

    assert progress.calculate_mastery_level() == MasteryLevel.MASTERED

def test_streak_achievements():
    achievements = AchievementPolicy.check_streak_achievements(7)
    assert any(a.id == "WEEK_STREAK" for a in achievements)
```

### Service Tests (Orchestration)
```python
@patch('infrastructure.repositories.ProgressRepository')
def test_record_session_completion(mock_repo):
    session_results = SessionResults(user_id="1", topic_id="topic-1", score=0.8)

    LearningAnalyticsService.record_session_completion(session_results)

    mock_repo.save_progress.assert_called_once()
```

### HTTP Tests (API Endpoints)
```python
def test_get_overall_progress_endpoint():
    response = client.get("/api/analytics/users/user-1/progress")

    assert response.status_code == 200
    data = response.json()
    assert "topics_completed" in data
    assert "average_score" in data
```

## Analytics Features

### Progress Tracking
- **Topic-level Progress**: Completion percentage, best score, time spent
- **Overall Progress**: Topics completed, learning velocity, consistency
- **Historical Trends**: Progress over time, learning patterns

### Achievement System
- **Streak Achievements**: Daily, weekly, monthly streaks
- **Mastery Achievements**: Topics mastered, perfect scores
- **Consistency Achievements**: Regular learning habits
- **Challenge Achievements**: Special learning challenges

### Learning Insights
- **Performance Analysis**: Strengths and areas for improvement
- **Learning Patterns**: Best learning times, session lengths
- **Recommendations**: Suggested topics, optimal study schedules
- **Goal Tracking**: Progress toward learning goals

## Anti-Patterns to Avoid

❌ **Active session management** (belongs in Learning Session module)
❌ **Topic content creation** (belongs in Content Creation module)
❌ **Real-time session state** (single session focus in Session module)
❌ **Business logic in HTTP routes**
❌ **Direct session management**

## Performance Considerations

- **Batch Processing**: Process multiple session results in batches
- **Caching**: Cache frequently accessed progress data
- **Aggregation**: Pre-calculate common metrics
- **Data Archiving**: Archive old session data for performance

## Module Evolution

This module can be extended with:
- **Advanced Analytics**: ML-based learning insights, predictive analytics
- **Social Features**: Leaderboards, peer comparisons, group challenges
- **Goal Management**: Custom learning goals, milestone tracking
- **Reporting**: Detailed progress reports, learning certificates
- **Integration**: Export data to external analytics platforms

The modular architecture ensures these features can be added without affecting active learning or content management functionality.
